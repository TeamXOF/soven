"""Offline regressions. No production database, credentials or providers are used."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import hashlib
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.test-deps'))
sys.path.insert(0, str(ROOT / 'backend'))
SANDBOX = tempfile.TemporaryDirectory()
os.environ.update(DATABASE_URL=str(Path(SANDBOX.name)/'regression.db'), OFFLINE_MODE='1',
                  GOOGLE_API_KEYS='', GOOGLE_API_KEY='', GROQ_API_KEY='', ENABLE_MOCK_ANALYSIS='0')
from database.schema import init_db, get_db_connection
from core.security import hash_password
from services.stt import TranscriptResult
from services import acoustic
from fastapi.testclient import TestClient
from main import app


class Regressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        with get_db_connection() as conn:
            for cid in ['a','b']:
                conn.execute('INSERT INTO classrooms(id,join_code) VALUES (?,?)',(cid,'code-'+cid))
                conn.execute('INSERT INTO students(id,name,grade,level,classroom_id) VALUES (?,?,3,?,?)',('s-'+cid,'Reader '+cid,'Level 1',cid))
                for role in ['teacher','student']:
                    uid=role+'-'+cid
                    conn.execute("INSERT INTO users(id,username,name,password_hash,role,status,student_id,classroom_id) VALUES (?,?,?,?,?,'approved',?,?)",(uid,uid,uid,hash_password('test-password-123'),role,'s-'+cid if role=='student' else None,cid))
                    conn.execute("INSERT INTO auth_tokens(token,user_id,expires_at) VALUES (?,?,datetime('now','+1 day'))",(uid,uid))
            conn.commit()
        cls.client=TestClient(app)

    def headers(self, role='teacher', classroom='a'):
        return {'Authorization':'Bearer '+role+'-'+classroom}

    def test_alignment_insertion_positions(self):
        for text in ['hello the cat sat','the cat hello sat','the cat sat hello']:
            words=[{'word':w,'start':i*.3,'end':(i+1)*.3,'probability':.95} for i,w in enumerate(text.split())]
            result=acoustic.build_signal('the cat sat',TranscriptResult(text=text,words=words),{'word_features':{},'total_duration':2,'pitch_variance':0},'en',0,0,0)
            self.assertEqual(result['accuracy'],75,text)
            self.assertEqual(sum(w.get('extra',False) for w in result['words']),1)

    def test_missing_confidence_stays_unknown(self):
        word={'word':'cat','start':0,'end':1,'probability':None}
        scored=acoustic.score_word(acoustic.align_words('cat',[word])[0],{'word_features':{}})
        self.assertIsNone(scored['recognition_confidence'])
        self.assertTrue(scored['correct'])

    def test_asr_doubt_and_pitch_do_not_become_reading_errors(self):
        word={'word':'cat','start':0,'end':1,'probability':.05}
        scored=acoustic.score_word(acoustic.align_words('cat',[word])[0],
            {'word_features':{(0.,1.):{'pitch_std':200,'rms':.001}}})
        self.assertTrue(scored['correct'])
        self.assertEqual(scored['score'],100)
        self.assertEqual(scored['recognition_confidence'],.05)

    def test_fresh_dashboard(self):
        response=self.client.get('/api/v1/students/s-a/dashboard',headers=self.headers())
        self.assertEqual(response.status_code,200,response.text)
        self.assertIn('summary',response.json())

    def test_authentication_required(self):
        for path in ['/api/students/','/api/sessions/','/api/v1/sessions','/api/v1/reports','/api/v1/sync/status']:
            self.assertEqual(self.client.get(path).status_code,401,path)

    def test_teacher_isolation_and_student_ownership(self):
        for headers in [self.headers('teacher'),self.headers('student')]:
            self.assertEqual(self.client.get('/api/students/s-b',headers=headers).status_code,403)
        ids={r['id'] for r in self.client.get('/api/students/',headers=self.headers()).json()}
        self.assertEqual(ids,{'s-a'})

    def test_dynamic_attempt_enters_teacher_reports(self):
        with get_db_connection() as conn:
            for suffix, student in [('a','s-a'),('b','s-b')]:
                conn.execute("INSERT OR REPLACE INTO story_levels(track,level,sentence) VALUES ('en',1,'The cat sat.')")
                conn.execute("INSERT OR REPLACE INTO story_attempts(id,student_id,track,level,accuracy,stars,passed,result_json) VALUES (?,?,'en',1,75,1,1,?)",('attempt-'+suffix,student,json.dumps({'words':[{'word':'cat','correct':False}], 'wpm':40,'transcript':'The dog sat'})))
            conn.commit()
        response=self.client.get('/api/v1/reports',headers=self.headers())
        self.assertEqual(response.status_code,200,response.text)
        reports=response.json()['reports']
        self.assertEqual([r['student_id'] for r in reports],['s-a'])
        self.assertGreaterEqual(reports[0]['checkpoints_attempted'],1)
        self.assertEqual(self.client.get('/api/v1/story/feedback/attempt-b',headers=self.headers('student')).status_code,403)

    def test_mock_disabled(self):
        response=self.client.post('/api/v1/story/analyze-mock',headers=self.headers('student'),json={'level':1,'words':['the']})
        self.assertEqual(response.status_code,404,response.text)

    def test_registration_requires_class_code(self):
        response=self.client.post('/api/auth/register',json={'name':'New reader','username':'new','password':'test-password-123'})
        self.assertEqual(response.status_code,422)
        response=self.client.post('/api/auth/register',json={'name':'New reader','username':'new','password':'test-password-123','classroom_code':'code-a'})
        self.assertEqual(response.status_code,200,response.text)

    def test_token_expiry(self):
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO auth_tokens(token,user_id,expires_at) VALUES ('expired','student-a','2000-01-01')")
            conn.commit()
        self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer expired'}).status_code,401)

    def test_migrations_repeat_without_loss(self):
        init_db()
        with get_db_connection() as conn:
            self.assertIsNotNone(conn.execute("SELECT id FROM students WHERE id='s-a'").fetchone())

    def test_startup_check_and_backup_connections_are_closed(self):
        import sqlite3
        from database import schema
        real_connect = sqlite3.connect
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / 'legacy.db')
            connection = real_connect(database)
            connection.execute('CREATE TABLE legacy_marker (id INTEGER)')
            connection.commit()
            connection.close()
            connections = []
            def track_connection(*args, **kwargs):
                connection = real_connect(*args, **kwargs)
                connections.append(connection)
                return connection
            with patch.object(schema, 'DB_PATH', database), patch.object(schema.sqlite3, 'connect', side_effect=track_connection):
                schema.init_db()  # Unversioned database and recovery backup.
                schema.init_db()  # Already versioned startup inspection.
            self.assertTrue((Path(directory) / '.db_backup/legacy-before-hardening.db').exists())
            self.assertGreaterEqual(len(connections), 5)
            for connection in connections:
                with self.assertRaises(sqlite3.ProgrammingError):
                    connection.execute('SELECT 1')

    def test_dynamic_detail_link(self):
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO story_attempts(id,student_id,track,level,accuracy,stars,passed,result_json) VALUES ('detail','s-a','en',1,80,2,1,?)", (json.dumps({'words':[], 'transcript':'The cat sat','wpm':42}),))
            conn.commit()
        response=self.client.get('/api/v1/sessions/detail',headers=self.headers())
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['totals']['avg_accuracy'],80)

    def test_mock_enabled_does_not_persist_progress(self):
        with get_db_connection() as conn:
            before=conn.execute('SELECT COUNT(*) FROM story_attempts').fetchone()[0]
        with patch.dict(os.environ,ENABLE_MOCK_ANALYSIS='1'):
            response=self.client.post('/api/v1/story/analyze-mock',headers=self.headers('student'),json={'track':'en','level':1,'words':['The','cat','sat']})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.json()['simulated'])
        with get_db_connection() as conn:
            self.assertEqual(before,conn.execute('SELECT COUNT(*) FROM story_attempts').fetchone()[0])

    def test_non_admin_cannot_change_server_keys(self):
        response=self.client.post('/api/v1/config/keys',headers=self.headers(),json={'google_api_keys':'invalid'})
        self.assertEqual(response.status_code,403)

    def test_invalid_auth_input_is_validation_error(self):
        response=self.client.post('/api/auth/login',json={'username':123,'password':[]})
        self.assertEqual(response.status_code,422)

    def test_actual_dynamic_request_saves_and_reports(self):
        text='The cat sat'
        words=[{'word':w,'start':i*.3,'end':(i+1)*.3,'probability':None} for i,w in enumerate(text.split())]
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO story_levels(track,level,sentence) VALUES ('en',1,?)",(text,))
            conn.commit()
        with patch('routers.story_mode.get_transcript',return_value=TranscriptResult(text=text,words=words)),patch('routers.story_mode.acoustic.extract_word_acoustics',return_value={'word_features':{},'total_duration':2,'pitch_variance':0}):
            response=self.client.post('/api/v1/story/analyze',headers=self.headers('student'),data={'track':'en','level':'1'},files={'audio':('reading.webm',b'\x1a\x45\xdf\xa3'+b'0'*1200,'audio/webm')})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['accuracy'],100)
        aid=response.json()['attempt_id']
        self.assertEqual(self.client.get('/api/v1/story/feedback/'+aid,headers=self.headers('student')).status_code,200)
        dashboard=self.client.get('/api/v1/students/s-a/dashboard',headers=self.headers()).json()
        self.assertGreater(dashboard['summary']['checkpoints_attempted'],0)

    def test_archive_keeps_history(self):
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO students(id,name,grade,classroom_id) VALUES ('archive','Archived',3,'a')")
            conn.execute("INSERT OR REPLACE INTO sessions(id,student_id,accuracy) VALUES ('archived-session','archive',0.8)")
            conn.commit()
        self.assertEqual(self.client.delete('/api/students/archive',headers=self.headers()).status_code,200)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute("SELECT archived FROM students WHERE id='archive'").fetchone()[0],1)
            self.assertIsNotNone(conn.execute("SELECT id FROM sessions WHERE id='archived-session'").fetchone())

    def test_sync_requires_ack_and_persists_retry(self):
        from services import sync_snapshots as sync
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO sessions(id,student_id,accuracy,synced) VALUES ('sync-failure','s-a',0.8,0)")
            conn.commit()
        bad=unittest.mock.Mock()
        bad.json.return_value={'ok':True}
        with patch.object(sync.settings,'CLOUD_SYNC_URL','https://example.invalid/ingest'),patch.dict(os.environ,SYNC_SHARED_SECRET='x'*32,OFFLINE_MODE='0'),patch.object(sync.requests,'post',return_value=bad):
            result=sync.push_queued()
        self.assertGreater(result['failed_count'],0)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute("SELECT synced FROM sessions WHERE id='sync-failure'").fetchone()[0],0)
            self.assertIsNotNone(conn.execute("SELECT * FROM sync_retries WHERE record_id='sync-failure'").fetchone())

    def test_sync_receiver_is_authenticated_and_idempotent(self):
        payload={'id':'external','student_id':'external-reader'}
        encoded=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'))
        digest=hashlib.sha256(encoded.encode()).hexdigest()
        packet={'source_id':'source','kind':'dynamic','record_id':'external','digest':digest,'payload':payload}
        self.assertEqual(self.client.post('/api/v1/sync/ingest',json=packet).status_code,401)
        with patch.dict(os.environ,SYNC_SHARED_SECRET='x'*32):
            for _ in range(2):
                response=self.client.post('/api/v1/sync/ingest',json=packet,headers={'Authorization':'Bearer '+'x'*32})
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.json()['digest'],digest)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM sync_received WHERE record_id='external'").fetchone()[0],1)

    def test_cloud_reasoning_has_a_local_fallback(self):
        import asyncio
        from agents.orchestrator import run_pipeline
        words=[{'word':'cat','start':0,'end':1,'probability':None}]
        result=asyncio.run(run_pipeline({'target_sentence':'cat','words_spoken':words,'wpm':60},[]))
        self.assertNotIn('error',result)
        self.assertEqual(result['engagement']['emotional_state'],'not_assessed')
        self.assertIsNotNone(result['practice']['sentences'])

    def test_real_acoustic_extraction_on_synthetic_wav(self):
        import wave
        import math
        import struct
        path=Path(SANDBOX.name)/'synthetic.wav'
        samples=[int(8000*math.sin(2*math.pi*220*i/16000)) for i in range(8000)]
        with wave.open(str(path),'wb') as wav:
            wav.setparams((1,2,16000,0,'NONE','not compressed'))
            wav.writeframes(struct.pack('<'+'h'*len(samples),*samples))
        result=acoustic.extract_word_acoustics(str(path),[{'word':'synthetic','start':0.05,'end':0.45}])
        self.assertAlmostEqual(result['total_duration'],0.5,places=2)
        self.assertTrue(math.isfinite(result['pitch_variance']))

    def test_whisper_decoder_api_is_compatible(self):
        import av
        import io
        import wave
        buffer=io.BytesIO()
        with wave.open(buffer,'wb') as wav:
            wav.setparams((1,2,16000,0,'NONE','not compressed'))
            wav.writeframes(b'\0'*3200)
        buffer.seek(0)
        with av.open(buffer,mode='r',metadata_errors='ignore') as container:
            self.assertGreater(sum(frame.samples for frame in container.decode(audio=0)),0)

    def test_unheard_recording_is_not_saved_as_failure(self):
        from services.stt import NoSpeechError
        with get_db_connection() as conn:
            before=conn.execute('SELECT COUNT(*) FROM story_attempts').fetchone()[0]
        with patch('routers.story_mode.get_transcript',side_effect=NoSpeechError('No speech was detected. Check your microphone and try again.')):
            response=self.client.post('/api/v1/story/analyze',headers=self.headers('student'),data={'track':'en','level':'1'},files={'audio':('silent.webm',b'0'*1200,'audio/webm')})
        self.assertEqual(response.status_code,422,response.text)
        self.assertIn('No speech',response.json()['error']['message'])
        with get_db_connection() as conn:
            self.assertEqual(before,conn.execute('SELECT COUNT(*) FROM story_attempts').fetchone()[0])

    def test_persistent_coaching_job_recovers(self):
        from services.jobs import enqueue,run_job
        key=enqueue('dynamic','job-recovery',['job-recovery','cat','en',{'words':[],'transcript':'cat','accuracy':100,'wpm':60,'hesitations':[]}])
        with patch('routers.story_mode._run_phase2',side_effect=RuntimeError('temporary failure')):
            run_job(key)
        with get_db_connection() as conn:
            row=conn.execute('SELECT status,attempts FROM coaching_jobs WHERE id=?',(key,)).fetchone()
            self.assertEqual((row['status'],row['attempts']),('pending',1))
            conn.execute('UPDATE coaching_jobs SET retry_after=0 WHERE id=?',(key,))
            conn.commit()
        run_job(key)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT status FROM coaching_jobs WHERE id=?',(key,)).fetchone()[0],'done')

    def test_socket_requires_auth_and_ownership(self):
        from routers.v1 import STORIES
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO story_sessions(id,student_id,story_id) VALUES ('socket','s-a',?)",(next(iter(STORIES)),))
            conn.commit()
        with self.client.websocket_connect('/ws/sessions/socket') as socket:
            socket.send_json({'token':'teacher-a'})
            self.assertEqual(socket.receive_json()['type'],'authenticated')
        from starlette.websockets import WebSocketDisconnect
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/ws/sessions/socket') as socket:
                socket.send_json({'token':'student-b'})
                socket.receive_json()

    def test_classic_recording_uses_word_accuracy(self):
        import base64
        signal={'transcript':'cat','words_spoken':[{'word':'cat','start':0,'end':1,'probability':None}],
                'wpm':60,'pauses':[],'grade':3,'target_sentence':'cat','language':'en'}
        with patch('routers.pipeline._process_audio',return_value=signal):
            response=self.client.post('/pipeline/run',headers=self.headers('student'),json={
                'student_id':'s-a','target_sentence':'cat','audio_base64':base64.b64encode(b'0'*1200).decode(),'language':'en'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['accuracy'],100)
        self.assertEqual(response.json()['overall_score'],100)
        self.assertEqual(response.json()['diagnosis']['phonetic']['status'],'available')
        self.assertEqual(response.json()['diagnosis']['progress']['source'],'measured_history')
        sessions=self.client.get('/api/sessions/',headers=self.headers('student')).json()
        self.assertEqual(next(s for s in sessions if s['id']==response.json()['session_id'])['language'],'en')
        self.assertIsInstance(response.json()['pauses'],int)
        with get_db_connection() as conn:
            row=conn.execute('SELECT accuracy,words_json FROM sessions WHERE id=?',(response.json()['session_id'],)).fetchone()
            self.assertEqual(row['accuracy'],1)
            self.assertTrue(json.loads(row['words_json']))

    def test_checkpoint_reread_generates_fresh_coaching(self):
        from routers.v1 import STORIES
        story=next(iter(STORIES.values()))
        checkpoint=story['checkpoints'][0]
        text=checkpoint['text_en']
        words=[{'word':w,'start':i*.3,'end':(i+1)*.3,'probability':None} for i,w in enumerate(text.split())]
        created=self.client.post('/api/v1/sessions',headers=self.headers('student'),json={'student_id':'s-a','story_id':story['id'],'language':'en'})
        self.assertEqual(created.status_code,201,created.text)
        sid=created.json()['session_id']
        with patch('routers.v1.get_transcript',return_value=TranscriptResult(text=text,words=words)),patch('routers.v1.acoustic.extract_word_acoustics',return_value={'word_features':{},'total_duration':3,'pitch_variance':0}):
            for _ in range(2):
                response=self.client.post(f'/api/v1/sessions/{sid}/analyze',headers=self.headers('student'),data={'checkpoint_id':checkpoint['id']},files={'audio':('read.webm',b'0'*1200,'audio/webm')})
                self.assertEqual(response.status_code,200,response.text)
        with get_db_connection() as conn:
            row=conn.execute('SELECT feedback_text,latency_json FROM checkpoint_results WHERE session_id=?',(sid,)).fetchone()
            self.assertTrue(row['feedback_text'])
            self.assertIn('stt',json.loads(row['latency_json']))
            jobs=conn.execute("SELECT COUNT(*) FROM coaching_jobs WHERE kind='checkpoint' AND arguments_json LIKE ?",('%'+sid+'%',)).fetchone()[0]
            self.assertEqual(jobs,2)


class DashboardFeedbackRegressions(unittest.TestCase):
    def signal(self, target="cat sat mat", spoken="dog sat mat", language="en"):
        words=[{'word':w,'start':i*.4,'end':(i+1)*.4,'probability':.9} for i,w in enumerate(spoken.split())]
        measured=acoustic.build_signal(target,TranscriptResult(text=spoken,words=words),
            {'word_features':{},'total_duration':2,'pitch_variance':0},language,0,0,0)
        return {**measured,'word_results':measured['words'],'words_spoken':words,
                'target_sentence':target,'language':language,'pause_count':len(measured['hesitations'])}

    def run_feedback(self, signal, history=None, provider=None):
        import asyncio
        from unittest.mock import AsyncMock
        from agents.orchestrator import run_pipeline
        with patch('agents.orchestrator.call_agent',new=AsyncMock(side_effect=provider) if provider else AsyncMock(return_value={'error':'offline'})):
            return asyncio.run(run_pipeline(signal,history or []))

    def test_urdu_punctuation_never_changes_word_match(self):
        for punctuation in ['۔','،','؟','!',',','.','؛']:
            result=self.signal('وہ یہاں تھا'+punctuation,'وہ یہاں تھا','ur')
            self.assertEqual(result['accuracy'],100,punctuation)
            self.assertEqual(len(result['words']),3)
        self.assertEqual(acoustic.tokenize('۔ ، ؟ !!!'),[])
        self.assertEqual(self.signal('تھا','تھا ۔','ur')['accuracy'],100)

    def test_unicode_words_preserve_letters_and_marks(self):
        self.assertEqual(acoustic.tokenize("Don't stop."),["Don't",'stop'])
        self.assertEqual(self.signal('café','cafe\u0301')['accuracy'],100)
        self.assertEqual(self.signal('طوطا','توتا','ur')['accuracy'],0)
        self.assertNotEqual(acoustic._norm('پڑھا'),acoustic._norm('پڑا'))

    def test_flagged_words_and_current_score_share_observations(self):
        signal=self.signal()
        result=self.run_feedback(signal)
        self.assertEqual(result['phonetic']['struggling_words'],['cat'])
        self.assertEqual(result['phonetic']['word_observations'],[w for w in signal['words'] if not w['correct']])
        self.assertEqual(result['progress']['current_accuracy'],signal['accuracy'])
        self.assertEqual(result['phonetic']['struggling_phonemes'],[])

    def test_current_low_score_overrides_strong_history(self):
        signal=self.signal()
        history=[{'accuracy':1,'wpm':100,'target_sentence':'cat sat mat','language':'en'}]*3
        result=self.run_feedback(signal,history)
        self.assertEqual(signal['accuracy'],67)
        self.assertTrue(all(s['difficulty']=='easy' for s in result['practice']['sentences']))
        self.assertTrue(all(acoustic._norm(s['target_word']) in [acoustic._norm(w) for w in acoustic.tokenize(s['text'])] for s in result['practice']['sentences']))

    def test_practice_difficulty_boundaries(self):
        for matched,total,tier in [(6,10,'easy'),(7,10,'medium'),(9,10,'hard'),(10,10,'hard')]:
            signal=self.signal()
            signal['target_sentence']=' '.join('word'+str(i) for i in range(total))
            signal['word_results']=[{'word':'word'+str(i),'spoken':'word'+str(i),'correct':i<matched} for i in range(total)]
            result=self.run_feedback(signal)
            self.assertEqual(result['practice']['difficulty_note'],tier)

    def test_generated_exercises_require_word_language_and_tier(self):
        invalid=[
            {'text':'The dog sat.','target_word':'cat','difficulty':'easy'},
            {'text':'The cat sat.','target_word':'cat','difficulty':'hard'},
            {'text':'The cattle sat.','target_word':'cat','difficulty':'easy'},
            {'text':'The dog sat.','target_word':'dog','difficulty':'easy'},
        ]
        for item in invalid:
            result=self.run_feedback(self.signal(),provider=lambda prompt,data:{'sentences':[item]})
            self.assertEqual(result['practice']['status'],'fallback')
        result=self.run_feedback(self.signal(),provider=lambda prompt,data:{'sentences':[{'text':'The cat sat.','target_word':'cat','difficulty':'easy'}]})
        self.assertEqual(result['practice']['source'],'model')
        self.assertEqual(result['practice']['status'],'available')
        ur=self.run_feedback(self.signal('وہ یہاں تھا','وہ وہاں تھا','ur'),provider=lambda prompt,data:{'sentences':[{'text':'Here is a cat.','target_word':'cat','difficulty':'easy'}]})
        self.assertEqual(ur['practice']['status'],'fallback')
        self.assertTrue(any('\u0600'<=c<='\u06ff' for c in ur['difficulty']['primary_issue']))

    def test_all_fallback_results_have_explicit_availability(self):
        result=self.run_feedback(self.signal())
        for block in result.values():
            self.assertIn(block['status'],{'available','fallback','unavailable'})
            self.assertTrue(block['source'])
        self.assertEqual(result['difficulty']['status'],'fallback')
        self.assertEqual(result['practice']['status'],'fallback')
        self.assertEqual(result['progress']['status'],'unavailable')
        self.assertEqual(result['engagement']['emotional_state'],'not_assessed')

    def test_estimated_timing_does_not_claim_zero_observed_pauses(self):
        signal=self.signal()
        signal['words_spoken'][0]['timing_source']='estimated'
        result=self.run_feedback(signal)
        self.assertEqual(result['engagement']['status'],'unavailable')
        self.assertIn('cannot be assessed',result['engagement']['teacher_note'])

    def test_progress_uses_latest_same_sentence_and_language(self):
        history=[
            {'accuracy':.1,'target_sentence':'Different words','language':'en','timestamp':'2026-10-31 12:03'},
            {'accuracy':.9,'target_sentence':'cat sat mat','language':'ur','timestamp':'2026-10-31 12:02'},
            {'accuracy':.5,'target_sentence':'cat sat mat.','language':'en','timestamp':'2026-10-31 12:01'},
            {'accuracy':1,'target_sentence':'cat sat mat','language':'en','timestamp':'2026-10-31 12:00'},
        ]
        result=self.run_feedback(self.signal(),history)['progress']
        self.assertEqual(result['previous_accuracy'],50)
        self.assertEqual(result['accuracy_change_points'],17)
        self.assertEqual(result['comparable_attempt_count'],3)
        self.assertEqual(result['source'],'measured_history')
        self.assertEqual(result['status'],'available')
        self.assertIsNone(result['improvement_percentage'])
        result=self.run_feedback(self.signal(),history[:2])['progress']
        self.assertEqual(result['status'],'unavailable')
        self.assertIsNone(result['previous_accuracy'])
        self.assertIn('same sentence',result['report_text'])


class EnrollmentRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client=TestClient(app)

    def setUp(self):
        self.classroom='enroll-'+uuid.uuid4().hex[:12]
        self.teacher='teacher-'+self.classroom
        self.code='join-'+self.classroom
        with get_db_connection() as conn:
            conn.execute('INSERT INTO classrooms(id,join_code) VALUES (?,?)',(self.classroom,self.code))
            conn.execute("INSERT INTO users(id,username,name,password_hash,role,status,classroom_id) VALUES (?,?,?,?,'teacher','approved',?)",
                (self.teacher,self.teacher,'Enrollment teacher',hash_password('enrollment-test-password'),self.classroom))
            conn.execute("INSERT INTO auth_tokens(token,user_id,expires_at) VALUES (?,?,datetime('now','+1 day'))",(self.teacher,self.teacher))
            conn.commit()
        self.headers={'Authorization':'Bearer '+self.teacher}

    def signup(self,suffix,name='Ayaan Khan'):
        username=self.classroom+'-'+suffix
        response=self.client.post('/api/auth/register',json={'name':name,'username':username,'password':'child-test-password','classroom_code':' '+self.code+' '})
        self.assertEqual(response.status_code,200,response.text)
        with get_db_connection() as conn:
            user=dict(conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone())
        self.assertEqual(user['status'],'pending')
        return user

    def profile(self,name='Ayaan Khan'):
        response=self.client.post('/api/students/',headers=self.headers,json={'name':name,'grade':5,'level':'Level 2'})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['id']

    def test_child_first_approval_creates_one_linked_profile(self):
        child=self.signup('new')
        login={'username':child['username'],'password':'child-test-password'}
        self.assertEqual(self.client.post('/api/auth/login',json=login).status_code,403)
        response=self.client.post('/api/auth/users/'+child['id']+'/approve',headers=self.headers)
        self.assertEqual(response.status_code,200,response.text)
        student_id=response.json()['student_id']
        self.assertTrue(response.json()['created_profile'])
        again=self.client.post('/api/auth/users/'+child['id']+'/approve',headers=self.headers)
        self.assertEqual(again.json()['student_id'],student_id)
        signed_in=self.client.post('/api/auth/login',json=login)
        self.assertEqual(signed_in.status_code,200,signed_in.text)
        self.assertEqual(signed_in.json()['user']['student_id'],student_id)
        roster=self.client.get('/api/v1/teacher/roster',headers=self.headers).json()
        # The API wraps the roster list for its current frontend contract.
        rows=roster['students'] if isinstance(roster,dict) else roster
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['account_username'],child['username'])
        self.assertEqual(rows[0]['id'],student_id)

    def test_existing_profile_is_linked_without_losing_history(self):
        student_id=self.profile()
        with get_db_connection() as conn:
            conn.execute("INSERT INTO sessions(id,student_id,accuracy) VALUES (?,?,.8)",('history-'+self.classroom,student_id))
            conn.commit()
        child=self.signup('existing')
        response=self.client.post('/api/auth/users/'+child['id']+'/approve',headers=self.headers,json={'student_id':student_id})
        self.assertEqual(response.status_code,200,response.text)
        self.assertFalse(response.json()['created_profile'])
        with get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM students WHERE classroom_id=?',(self.classroom,)).fetchone()[0],1)
            profile=conn.execute('SELECT grade,level FROM students WHERE id=?',(student_id,)).fetchone()
            self.assertEqual((profile['grade'],profile['level']),(5,'Level 2'))
            self.assertEqual(conn.execute('SELECT student_id FROM sessions WHERE id=?',('history-'+self.classroom,)).fetchone()[0],student_id)
            self.assertEqual(conn.execute('SELECT student_id FROM users WHERE id=?',(child['id'],)).fetchone()[0],student_id)

    def test_linking_rejects_occupied_archived_and_foreign_profiles(self):
        student_id=self.profile()
        first=self.signup('first')
        target='/api/auth/users/'+first['id']+'/approve'
        self.assertEqual(self.client.post(target,headers=self.headers,json={'student_id':student_id}).status_code,200)
        second=self.signup('second')
        target='/api/auth/users/'+second['id']+'/approve'
        self.assertEqual(self.client.post(target,headers=self.headers,json={'student_id':student_id}).status_code,409)
        archived=self.profile('Archived reader')
        self.client.delete('/api/students/'+archived,headers=self.headers)
        # Ownership middleware hides archived profiles before the approval handler.
        self.assertEqual(self.client.post(target,headers=self.headers,json={'student_id':archived}).status_code,404)
        foreign='foreign-'+self.classroom
        with get_db_connection() as conn:
            conn.execute('INSERT INTO classrooms(id,join_code) VALUES (?,?)',(foreign,foreign))
            conn.execute('INSERT INTO students(id,name,grade,classroom_id) VALUES (?, ?,3,?)',(foreign,'Other classroom child',foreign))
            conn.commit()
        self.assertEqual(self.client.post(target,headers=self.headers,json={'student_id':foreign}).status_code,403)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT status FROM users WHERE id=?',(second['id'],)).fetchone()[0],'pending')

    def test_two_signups_cannot_claim_one_profile_concurrently(self):
        from concurrent.futures import ThreadPoolExecutor
        student_id=self.profile()
        children=[self.signup('race-'+str(i)) for i in range(2)]
        def approve(child):
            return self.client.post('/api/auth/users/'+child['id']+'/approve',headers=self.headers,json={'student_id':student_id}).status_code
        with ThreadPoolExecutor(2) as pool:
            statuses=list(pool.map(approve,children))
        self.assertEqual(sorted(statuses),[200,409])
        with get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM users WHERE student_id=?',(student_id,)).fetchone()[0],1)

    def test_approved_account_cannot_be_reassigned(self):
        child=self.signup('fixed')
        target='/api/auth/users/'+child['id']+'/approve'
        original=self.client.post(target,headers=self.headers,json={}).json()['student_id']
        other=self.profile('Different child')
        response=self.client.post(target,headers=self.headers,json={'student_id':other})
        self.assertEqual(response.status_code,409,response.text)
        with get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT student_id FROM users WHERE id=?',(child['id'],)).fetchone()[0],original)


if __name__=='__main__':
    unittest.main(verbosity=2)
