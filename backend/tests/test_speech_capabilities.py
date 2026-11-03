"""Speech contracts with mocked adapters, synthetic audio and isolated HTTP/SQLite."""
import asyncio
import base64
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as Obj
import unittest
from unittest.mock import patch,Mock
import wave

# Reuse the isolated database/empty-key fixture, not its test class discovery.
import test_regressions as fixtures
from services import stt,acoustic
from core import speech_capabilities as capabilities
from fastapi import HTTPException

class Contracts(unittest.TestCase):
    def setUp(self):
        self.audio=tempfile.NamedTemporaryFile(suffix='.wav',delete=False);self.audio.write(b'fake-audio');self.audio.close()
        self.addCleanup(lambda:Path(self.audio.name).unlink(missing_ok=True))
    def response(self,data):return Obj(ok=True,json=lambda:data)
    def local(self):return stt.TranscriptResult(text='cat',words=stt._normalize_words([],'cat'),engine='test')
    def evidence(self,words):return capabilities.observed_speech_evidence(stt.TranscriptResult(text='a b',words=words),'en')

    def test_language_routes_are_canonical_and_isolated(self):
        code,policy=capabilities.speech_policy('UR_pk');self.assertEqual(code,'ur');self.assertEqual(policy['locale'],'ur-PK')
        policy['recognition'].clear();self.assertTrue(capabilities.speech_policy('ur')[1]['recognition'])
        self.assertEqual(set(capabilities.language_speech_inventory()['languages']),{'en','ur','es'})
    def test_planned_language_rejected_before_any_provider_or_probe(self):
        with patch.object(stt,'network_available') as net,patch.object(stt,'groq_whisper') as cloud,patch.object(stt,'local_whisper') as local:
            for lang in ['fr','ar','../en']:
                with self.assertRaises(HTTPException):stt.get_transcript(self.audio.name,lang)
            net.assert_not_called();cloud.assert_not_called();local.assert_not_called()
    def test_forced_local_never_probes_or_calls_cloud(self):
        with patch.dict(os.environ,OFFLINE_MODE='1'),patch.object(stt,'network_available') as net,patch.object(stt,'groq_whisper') as cloud,patch.object(stt,'local_whisper',return_value=self.local()) as local:
            result=stt.get_transcript(self.audio.name,'ur-PK')
            self.assertEqual(result.fallback_reason,'forced_local');self.assertEqual(local.call_args.args[1],'ur')
            net.assert_not_called();cloud.assert_not_called()
    def test_missing_key_uses_local_without_network_probe(self):
        with patch.dict(os.environ,OFFLINE_MODE='0',STT_MODE='auto'),patch.object(stt.settings,'GROQ_API_KEY',''),patch.object(stt,'network_available') as net,patch.object(stt,'local_whisper',return_value=self.local()):
            self.assertEqual(stt.get_transcript(self.audio.name).fallback_reason,'no_groq_key');net.assert_not_called()
    def test_cloud_success_does_not_invoke_local(self):
        with patch.dict(os.environ,OFFLINE_MODE='0',STT_MODE='auto'),patch.object(stt.settings,'GROQ_API_KEY','synthetic'),patch.object(stt,'network_available',return_value=True),patch.object(stt,'groq_whisper',return_value=self.local()),patch.object(stt,'local_whisper') as local:
            stt.get_transcript(self.audio.name);local.assert_not_called()
    def test_cloud_failure_falls_back_with_redacted_reason(self):
        with patch.dict(os.environ,OFFLINE_MODE='0',STT_MODE='groq'),patch.object(stt.settings,'GROQ_API_KEY','synthetic'),patch.object(stt,'network_available',return_value=True),patch.object(stt,'groq_whisper',side_effect=RuntimeError('private-content')),patch.object(stt,'local_whisper',return_value=self.local()):
            result=stt.get_transcript(self.audio.name);self.assertEqual(result.fallback_reason,'groq: RuntimeError')
    def test_no_speech_does_not_retry_as_another_recognizer(self):
        with patch.dict(os.environ,OFFLINE_MODE='0',STT_MODE='auto'),patch.object(stt.settings,'GROQ_API_KEY','synthetic'),patch.object(stt,'network_available',return_value=True),patch.object(stt,'groq_whisper',side_effect=stt.NoSpeechError('silence')),patch.object(stt,'local_whisper') as local:
            with self.assertRaises(stt.NoSpeechError):stt.get_transcript(self.audio.name)
            local.assert_not_called()
    def test_cloud_segment_only_text_has_no_invented_timings(self):
        data={'text':'وہ یہاں تھا۔','segments':[{'start':0,'end':3,'text':'وہ یہاں تھا۔'}]}
        with patch('requests.post',return_value=self.response(data)) as send:
            result=stt.groq_whisper(self.audio.name,'ur')
        self.assertEqual([w['word'] for w in result.words],['وہ','یہاں','تھا'])
        self.assertTrue(all(w['start'] is None and w['end'] is None and w['probability'] is None for w in result.words))
        self.assertNotIn('prompt',dict(send.call_args.kwargs['data']))
        self.assertEqual(capabilities.observed_speech_evidence(result,'ur')['pause_assessment'],'unavailable')
    def test_cloud_text_only_remains_scoreable(self):
        with patch('requests.post',return_value=self.response({'text':'The cat sat.'})):
            result=stt.groq_whisper(self.audio.name)
        signal=acoustic.build_signal('The cat sat.',result,{'total_duration':3,'pitch_variance':None},'en',0,0,0)
        self.assertEqual(signal['accuracy'],100);self.assertEqual(signal['wpm'],60)
        self.assertEqual(signal['speech_evidence']['word_timing'],'unavailable')
    def test_invalid_timing_and_probability_stay_unavailable(self):
        words=stt._normalize_words([{'word':'a','start':float('nan'),'end':2,'probability':float('inf')},
            {'word':'b','start':2,'end':1,'probability':-1},{'word':'c','start':0,'end':1,'probability':.5,'timing_source':'estimated'}])
        self.assertTrue(all(w['start'] is None for w in words));self.assertEqual(words[2]['probability'],.5)
        self.assertEqual(self.evidence(words)['recognition_confidence'],'partial')
    def test_partial_timing_cannot_claim_complete_pause_assessment(self):
        evidence=self.evidence([{'word':'a','start':0,'end':1},{'word':'b','start':None,'end':None}])
        self.assertEqual(evidence['word_timing'],'partial');self.assertEqual(evidence['timed_word_count'],1)
        self.assertEqual(evidence['pause_assessment'],'unavailable')
    def test_overlapping_or_single_words_cannot_claim_pause_assessment(self):
        for words in [[{'word':'a','start':0,'end':1}],
                      [{'word':'a','start':0,'end':2},{'word':'b','start':1,'end':3}]]:
            self.assertEqual(self.evidence(words)['pause_assessment'],'unavailable')
    def test_pause_detection_never_bridges_missing_word(self):
        words=[{'word':'a','start':0,'end':.2},{'word':'b','start':None,'end':None},{'word':'c','start':2,'end':3}]
        self.assertEqual(acoustic.detect_hesitations(words),[])
        self.assertEqual(acoustic.detect_hesitations([words[0],words[2]])[0]['pause_ms'],1800)
    def test_complete_real_timing_and_confidence_are_reported(self):
        row=self.evidence([{'word':'a','start':0,'end':1,'probability':.4},{'word':'b','start':2,'end':3,'probability':.8}])
        self.assertEqual(row['word_timing'],'available');self.assertEqual(row['recognition_confidence'],'available')
        self.assertEqual(row['pause_assessment'],'available');self.assertFalse(row['quality_validated'])
    def test_out_of_clip_timing_does_not_create_pauses(self):
        result=stt.TranscriptResult(text='cat sat',words=[{'word':'cat','start':0,'end':1},{'word':'sat','start':3,'end':4}])
        signal=acoustic.build_signal('cat sat',result,{'total_duration':2,'pitch_variance':None},'en',0,0,0)
        self.assertEqual(signal['speech_evidence']['word_timing'],'partial')
        self.assertEqual(signal['hesitations'],[]);self.assertEqual(signal['engagement_state'],'unknown')
        self.assertFalse(capabilities.has_word_timing({'start':0,'end':1,'timing_source':'segment'}))

    def test_mock_timings_are_explicitly_simulation(self):
        result=self.local();result.fallback_reason='mock';result.words=[{'word':'cat','start':0,'end':1,'probability':.9}]
        evidence=capabilities.observed_speech_evidence(result,'en')
        self.assertEqual(evidence['origin'],'simulation');self.assertEqual(evidence['word_timing'],'unavailable')
    def test_faster_whisper_segment_fallback_has_no_word_timing(self):
        model=Obj(transcribe=Mock(return_value=([Obj(words=None,text='cat sat',start=1,end=3)],None)))
        stt._get_local_whisper.cache_clear();self.addCleanup(stt._get_local_whisper.cache_clear)
        with patch.dict(sys.modules,{'faster_whisper':Obj(WhisperModel=lambda *a,**k:model)}):
            result=stt.local_whisper(self.audio.name,'en')
        self.assertEqual(result.engine,'faster_whisper');self.assertTrue(all(w['start'] is None for w in result.words))
        self.assertNotIn('initial_prompt',model.transcribe.call_args.kwargs)
    def test_openai_whisper_preserves_untimed_segments(self):
        model=Obj(transcribe=Mock(return_value={'text':'cat sat','segments':[{'text':'cat','words':[{'word':'cat','start':0,'end':1}]},{'text':'sat'}]}))
        stt._get_local_whisper.cache_clear();self.addCleanup(stt._get_local_whisper.cache_clear)
        with patch.dict(sys.modules,{'faster_whisper':Obj(WhisperModel=Mock(side_effect=ImportError())), 'whisper':Obj(load_model=lambda *a:model)}),patch.dict(os.environ,OFFLINE_MODE='0'):
            result=stt.local_whisper(self.audio.name,'en')
        self.assertEqual(result.engine,'openai_whisper');self.assertEqual([w['word'] for w in result.words],['cat','sat'])
        self.assertIsNone(result.words[1]['start'])
    def test_no_timing_still_measures_clip_duration_without_pitch(self):
        with wave.open(self.audio.name,'wb') as audio:
            audio.setparams((1,2,16000,0,'NONE','not compressed'));audio.writeframes(b'\0'*16000)
        with patch('librosa.yin') as pitch:
            result=acoustic.extract_word_acoustics(self.audio.name,stt._normalize_words([],'cat sat'))
        self.assertEqual(result['word_features'],{});self.assertIsNone(result['pitch_variance']);pitch.assert_not_called()
        self.assertEqual(result['total_duration'],.5)
    def test_coaching_reports_unavailable_pauses(self):
        from agents.orchestrator import run_pipeline
        result=asyncio.run(run_pipeline({'target_sentence':'cat sat','words_spoken':stt._normalize_words([],'cat sat'),'wpm':60},[]))
        self.assertEqual(result['engagement']['status'],'unavailable')
        self.assertNotIn('0.',result['engagement']['teacher_note'])

class HttpContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.Regressions.setUpClass();cls.client=fixtures.Regressions.client
    headers=fixtures.Regressions.headers
    def words(self):return stt.TranscriptResult(text='The cat sat',words=stt._normalize_words([],'The cat sat'),engine='synthetic_adapter')
    def features(self):return {'word_features':{},'total_duration':2,'pitch_variance':None}
    def test_public_inventory_contains_routes_without_private_configuration(self):
        response=self.client.get('/api/v1/capabilities');self.assertEqual(response.status_code,200)
        self.assertEqual(set(response.json()['language_speech']['languages']),{'en','ur','es'})
        self.assertNotIn('synthetic_adapter',response.text)
    def test_additive_evidence_migration_is_idempotent(self):
        fixtures.init_db();fixtures.init_db()
        with fixtures.get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM schema_migrations WHERE version=4').fetchone()[0],1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students WHERE id='s-a'").fetchone()[0],1)
    def test_classic_missing_timing_is_persisted_and_scoped(self):
        with patch('services.stt.get_transcript',return_value=self.words()),patch('services.acoustic.extract_word_acoustics',return_value=self.features()):
            response=self.client.post('/pipeline/run',headers=self.headers('student'),json={'student_id':'s-a','target_sentence':'The cat sat','language':'en','audio_base64':base64.b64encode(b'x'*1200).decode()})
        self.assertEqual(response.status_code,200,response.text);row=response.json()
        self.assertEqual(row['accuracy'],100);self.assertIsNone(row['pauses'])
        detail=self.client.get('/api/sessions/'+row['session_id']+'/diagnosis',headers=self.headers('student'))
        self.assertEqual(detail.json()['speech_evidence']['word_timing'],'unavailable')
        self.assertEqual(self.client.get('/api/sessions/'+row['session_id']+'/diagnosis',headers=self.headers('student','b')).status_code,403)
    def test_checkpoint_evidence_survives_history_and_reread(self):
        from routers.v1 import STORIES
        story=next(iter(STORIES.values()));cp=story['checkpoints'][0]
        created=self.client.post('/api/v1/sessions',headers=self.headers('student'),json={'student_id':'s-a','story_id':story['id'],'language':'en'})
        sid=created.json()['session_id']
        with patch('routers.v1.get_transcript',return_value=self.words()),patch('services.acoustic.extract_word_acoustics',return_value=self.features()):
            for _ in range(2):
                response=self.client.post('/api/v1/sessions/'+sid+'/analyze',headers=self.headers('student'),data={'checkpoint_id':cp['id']},files={'audio':('read.webm',b'x'*1200,'audio/webm')})
                self.assertEqual(response.status_code,200,response.text);self.assertEqual(response.json()['speech_evidence']['pause_assessment'],'unavailable')
        detail=self.client.get('/api/v1/sessions/'+sid,headers=self.headers('student')).json()
        self.assertEqual(detail['checkpoints'][0]['speech_evidence']['engine'],'synthetic_adapter')
        with fixtures.get_db_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM speech_evidence WHERE record_kind='checkpoint' AND record_id NOT IN (SELECT id FROM checkpoint_results)").fetchone()[0],0)
    def test_dynamic_evidence_survives_history(self):
        with fixtures.get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO story_levels(track,level,sentence) VALUES ('en',1,'The cat sat')");conn.commit()
        with patch('routers.story_mode.get_transcript',return_value=self.words()),patch('services.acoustic.extract_word_acoustics',return_value=self.features()):
            response=self.client.post('/api/v1/story/analyze',headers=self.headers('student'),data={'track':'en','level':'1'},files={'audio':('read.webm',b'x'*1200,'audio/webm')})
        self.assertEqual(response.status_code,200,response.text)
        detail=self.client.get('/api/v1/sessions/'+response.json()['attempt_id'],headers=self.headers('student')).json()
        self.assertEqual(detail['checkpoints'][0]['speech_evidence']['word_timing'],'unavailable')
    def test_legacy_evidence_is_unknown_not_reconstructed(self):
        with fixtures.get_db_connection() as conn:
            conn.execute("INSERT INTO sessions(id,student_id,target_sentence,transcript) VALUES ('legacy-speech','s-a','cat','cat')")
            conn.execute("INSERT INTO diagnoses(session_id) VALUES ('legacy-speech')");conn.commit()
        row=self.client.get('/api/sessions/legacy-speech/diagnosis',headers=self.headers('student')).json()
        self.assertIsNone(row['speech_evidence'])

if __name__=='__main__':unittest.main(verbosity=2)
