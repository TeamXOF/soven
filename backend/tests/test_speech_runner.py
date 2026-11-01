"""Deterministic metrics and failure-path tests; fake workers, synthetic input."""
from copy import deepcopy
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from core import speech_evaluation as evaluation
from core import speech_runner as runner
from core import speech_metrics as metrics


class Worker:
    model_load_ms=7
    calls=[]
    closed=0
    def __init__(self,*args): pass
    def transcribe(self,audio,language):
        self.calls.append((audio,language))
        return {'text':'The dog sat.','words':[{'word':w} for w in ['The','dog','sat']],
                'audio_seconds':2,'timing_source':'unavailable','asr_invoked':True}
    def close(self):type(self).closed+=1


class MetricsContracts(unittest.TestCase):
    def setUp(self):
        self.protocol=runner.load_protocol()

    def test_edit_counts_known_substitution_deletion_and_insertion(self):
        value=metrics.edit_counts('a b c','a x c d')
        self.assertEqual((value['substitutions'],value['deletions'],value['insertions']),(1,0,1))
        self.assertAlmostEqual(value['wer'],2/3)
        self.assertEqual(metrics.edit_counts('a b c','a c')['deletions'],1)
        self.assertEqual(metrics.edit_counts('go go','go')['edits'],1)

    def test_unicode_normalization_ignores_urdu_punctuation_preserves_letters(self):
        self.assertEqual(metrics.edit_counts('وہ یہاں تھا۔','وہ، یہاں تھا؟')['edits'],0)
        self.assertEqual(metrics.edit_counts('café','cafe\u0301')['edits'],0)
        self.assertEqual(metrics.edit_counts('طوطا','توتا')['substitutions'],1)

    def test_wer_can_exceed_one_and_empty_reference_is_unavailable(self):
        self.assertEqual(metrics.edit_counts('cat','dog sat here')['wer'],3)
        self.assertIsNone(metrics.edit_counts('','hello')['wer'])
        with self.assertRaises(ValueError):metrics.edit_counts('a b','a',maximum_tokens=1)

    def clip(self):
        return {'id':'one','speaker_id':'one','language':'en','age_band':'child','device':'phone','noise':'quiet',
                'reference_text':'The dog sat.','target_text':'The cat sat.','target_word_matches':[True,False,True]}

    def result(self,text):return {'text':text,'words':[{'word':w} for w in text.split()]}

    def test_flags_compare_adjudicated_target_positions_not_asr_confidence(self):
        result=self.result('The dog sat.')
        for word in result['words']:word['probability']=.01
        row=metrics.score_clip(self.clip(),result,'development',self.protocol)
        self.assertEqual(row['asr_counts']['wer'],0)
        self.assertEqual(row['target_flags'],[False,True,False])
        self.assertEqual(row['flag_counts'],{'matching':2,'differing':1,'false_flags':0,'differing_flagged':1})

    def test_insertions_are_visible_without_falsely_flagging_matched_targets(self):
        clip=self.clip();clip.update(target_text='The dog sat.',reference_text='Hello the dog sat.',target_word_matches=[True]*3)
        row=metrics.score_clip(clip,self.result('Hello the dog sat.'),'controls',self.protocol)
        self.assertEqual(row['asr_counts']['wer'],0)
        self.assertEqual(row['extra_words'],['Hello'])
        self.assertEqual(row['flag_counts']['false_flags'],0)

    def test_word_ending_difference_remains_flagged(self):
        clip=self.clip();clip.update(target_text='The cats jumped.',reference_text='The cats jump.',target_word_matches=[True,True,False])
        row=metrics.score_clip(clip,self.result('The cats jump.'),'controls',self.protocol)
        self.assertEqual(row['target_flags'],[False,False,True])

    def test_historical_comparison_never_labels_prompt_edit_rate_as_wer(self):
        clip=self.clip();clip.update(reference_text='The cat sat.',expert_word_labels=[{'text':'The','accuracy':9},
            {'text':'cat','accuracy':9},{'text':'sat','accuracy':5}])
        row=metrics.score_clip(clip,self.result('The dog sat.'),'historical',self.protocol)
        summary=metrics.summarize([row],'historical',self.protocol)
        self.assertNotIn('asr_counts',row)
        self.assertNotIn('wer',row['prompt_counts'])
        self.assertAlmostEqual(summary['prompt_text_edit_rate'],1/3)
        self.assertEqual(summary['historical_expert_comparison']['expert_acceptable_model_flag'],1)
        self.assertEqual(summary['historical_expert_comparison']['expert_error_model_accept'],1)

    def test_unmatched_historical_word_labels_are_not_silently_dropped(self):
        clip=self.clip();clip['expert_word_labels']=[{'text':'different','accuracy':9}]
        row=metrics.score_clip(clip,self.result('The dog sat.'),'historical',self.protocol)
        self.assertEqual(row['historical_expert_comparison']['unmatched_word_labels'],3)

    def test_failed_clips_remain_visible_and_block_release(self):
        row=metrics.score_clip(self.clip(),self.result('The dog sat.'),'development',self.protocol)
        failed={**self.clip(),'status':'failed'}
        summary=metrics.summarize([row,failed],'development',self.protocol)
        self.assertEqual((summary['scheduled'],summary['completed'],summary['failed']),(2,1,1))
        self.assertFalse(summary['failure_free'])
        self.assertEqual(summary['wer_on_completed'],0)

    def test_zero_denominators_are_not_perfect_recall(self):
        summary=metrics.summarize([],'development',self.protocol)
        self.assertIsNone(summary['wer_on_completed'])
        self.assertIsNone(summary['reference_difference_recall_on_completed'])
        self.assertFalse(metrics.threshold_checks(summary,evaluation.load_profile()['language_criteria']['en'])['difference_recall'])

    def test_speaker_macro_does_not_let_prolific_speaker_dominate(self):
        row=metrics.score_clip(self.clip(),self.result('The dog sat.'),'development',self.protocol)
        one=deepcopy(row);one['speaker_id']='a';one['asr_counts'].update(edits=0,reference_words=100)
        two=deepcopy(row);two['speaker_id']='b';two['asr_counts'].update(edits=1,reference_words=1)
        summary=metrics.summarize([one,two],'development',self.protocol)
        self.assertAlmostEqual(summary['wer_on_completed'],1/101)
        self.assertEqual(summary['mean_speaker_wer_on_completed'],.5)

    def test_speaker_bootstrap_is_reproducible_and_unavailable_for_one_speaker(self):
        row=metrics.score_clip(self.clip(),self.result('The dog sat.'),'development',self.protocol)
        self.assertFalse(metrics.summarize([row],'development',self.protocol)['speaker_bootstrap']['available'])
        other=deepcopy(row);other['speaker_id']='two';other['asr_counts']['edits']=1
        first=metrics.summarize([row,other],'development',self.protocol)['speaker_bootstrap']
        second=metrics.summarize([row,other],'development',self.protocol)['speaker_bootstrap']
        self.assertEqual(first,second)
        self.assertEqual(first['intervals']['wer']['lower'],0)
        self.assertAlmostEqual(first['intervals']['wer']['upper'],1/3)

    def test_holdout_screening_requires_every_cohort_and_no_failed_clip(self):
        profile=evaluation.load_profile()
        template=metrics.score_clip(self.clip(),self.result('The dog sat.'),'development',self.protocol)
        rows=[]
        for speaker in range(30):
            for take in range(3):
                row=deepcopy(template)
                row.update(id=f'{speaker}-{take}',speaker_id=str(speaker),age_band='child' if speaker<15 else 'adult',
                           device='phone' if speaker<15 else 'desktop',noise='quiet' if speaker<15 else 'background')
                rows.append(row)
        coverage={'en':{'release_sample_eligible':True}}
        report=metrics.summarize_run(rows,'holdout',profile,self.protocol,coverage)
        self.assertTrue(report['release_review_eligible'])
        self.assertFalse(report['quality_validated'])
        rows[0]['status']='failed'
        report=metrics.summarize_run(rows,'holdout',profile,self.protocol,coverage)
        self.assertFalse(report['release_review_eligible'])
        self.assertFalse(report['languages']['en']['cohorts']['age_band:child']['checks']['failure_free'])

    def test_controls_and_development_never_become_release_evidence(self):
        profile=evaluation.load_profile()
        row=metrics.score_clip(self.clip(),self.result('The dog sat.'),'development',self.protocol)
        for mode in ['controls','development']:
            report=metrics.summarize_run([row],mode,profile,self.protocol,{'en':{'release_sample_eligible':True}})
            self.assertFalse(report['release_review_eligible'])
            self.assertFalse(report['quality_validated'])


class RunnerContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.ledger=self.root/'exposure.sqlite3'
        self.profile=evaluation.load_profile()
        self.frozen=evaluation.seal({'profile':self.profile,'kind':'speech_baseline_freeze'})
        for module in [evaluation,runner]:
            mocked=patch.object(module,'verify_freeze');mocked.start();self.addCleanup(mocked.stop)
        Worker.calls=[];Worker.closed=0

    def dataset(self,name='data',split='development',speaker='reader',policy='controls',count=1):
        folder=self.root/name;folder.mkdir(exist_ok=True)
        rows=[]
        for index in range(count):
            audio=folder/f'{index}.wav';audio.write_bytes(f'synthetic-{name}-{index}'.encode())
            rows.append({'id':f'clip{index}','speaker_id':speaker,'language':'en',
                'age_band':'adult','device':'desktop','noise':'quiet','audio_path':audio.name,
                'audio_sha256':evaluation.file_hash(audio),'target_text':'The cat sat.','reference_text':'The dog sat.',
                'reference_kind':'synthetic_script' if policy=='controls' else 'verbatim',
                'reference_review':'scripted' if policy=='controls' else 'adjudicated',
                'target_word_matches':[True,False,True]})
        data={'schema_version':1,'corpus_id':'synthetic-runner-fixture','split':split,
              'rights_basis':'Synthetic bytes, fake worker; no human audio','clips':rows}
        path=folder/'manifest.json';path.write_text(json.dumps(data),encoding='utf-8')
        return path,data

    def run_case(self,path,mode='controls',name='report.json',**kwargs):
        return runner.run_evaluation(path,mode,self.frozen,self.root/'model',self.root/name,self.ledger,
                                     preflight_model=False,**kwargs)

    def test_full_control_run_passes_only_audio_and_language_to_worker(self):
        path,_=self.dataset()
        report=self.run_case(path,worker_factory=Worker)
        self.assertEqual(report['status'],'completed')
        self.assertEqual(Worker.calls,[(b'synthetic-data-0','en')])
        self.assertEqual(Worker.closed,1)
        evaluation.verify_seal(report)
        self.assertFalse(report['summary']['release_review_eligible'])
        with closing(sqlite3.connect(self.ledger)) as connection:
            self.assertEqual(connection.execute('SELECT status FROM runs').fetchone()[0],'completed')

    def test_model_drift_fails_before_worker_or_output(self):
        path,_=self.dataset();factory=Mock()
        with patch.object(runner,'freeze_baseline',side_effect=ValueError('model drift')):
            with self.assertRaises(ValueError):
                runner.run_evaluation(path,'controls',self.frozen,self.root/'model',self.root/'report.json',self.ledger,worker_factory=factory)
        factory.assert_not_called();self.assertFalse((self.root/'report.json').exists())

    def test_human_mode_cannot_accept_synthetic_script_references(self):
        path,_=self.dataset();factory=Mock()
        with self.assertRaises(ValueError):self.run_case(path,mode='development',worker_factory=factory)
        factory.assert_not_called()

    def test_output_cannot_overwrite_an_existing_report(self):
        path,_=self.dataset();target=self.root/'report.json';target.write_text('previous')
        with self.assertRaises(FileExistsError):self.run_case(path,worker_factory=Worker)
        self.assertEqual(target.read_text(),'previous');self.assertEqual(Worker.calls,[])

    def test_clip_failure_is_retained_and_later_clip_can_succeed(self):
        path,_=self.dataset(count=2)
        class FailOnce(Worker):
            def transcribe(self,audio,language):
                if audio.endswith(b'-0'):raise ValueError('private-text-must-not-be-logged')
                return super().transcribe(audio,language)
        report=self.run_case(path,worker_factory=FailOnce)
        self.assertEqual([row['status'] for row in report['clips']],['failed','ok'])
        self.assertNotIn('private-text',json.dumps(report))
        self.assertEqual(report['summary']['languages']['en']['failed'],1)

    def test_repeated_failures_mark_remaining_clips_not_run(self):
        path,_=self.dataset(count=5)
        class Broken(Worker):
            def transcribe(self,*args):raise ValueError('decode failure')
        report=self.run_case(path,worker_factory=Broken)
        self.assertEqual([row['status'] for row in report['clips']],['failed']*3+['not_run']*2)

    def test_worker_timeout_stops_further_processing(self):
        path,_=self.dataset(count=2)
        class Timeout(Worker):
            def transcribe(self,*args):raise runner.ClipFailure('WorkerTimeout')
        report=self.run_case(path,worker_factory=Timeout)
        self.assertEqual([row['status'] for row in report['clips']],['failed','not_run'])

    def test_initialization_failure_and_interruption_are_visible(self):
        path,_=self.dataset(count=2)
        report=self.run_case(path,worker_factory=Mock(side_effect=ValueError('private-model-path')))
        self.assertEqual([row['status'] for row in report['clips']],['not_run']*2)
        class Interrupted(Worker):
            def transcribe(self,*args):raise KeyboardInterrupt()
        report=self.run_case(path,name='interrupt.json',worker_factory=Interrupted)
        self.assertEqual([row['status'] for row in report['clips']],['not_run']*2)
        evaluation.verify_seal(report)

    def holdout(self):
        dev,_=self.dataset('dev','development','dev-reader','human')
        hold,_=self.dataset('hold','holdout','new-reader','human')
        registered=evaluation.register_evaluation(dev,hold,self.frozen)
        return dev,hold,registered

    def test_holdout_requires_matching_preregistration(self):
        dev,hold,registered=self.holdout()
        with self.assertRaises(ValueError):self.run_case(hold,mode='holdout',worker_factory=Worker)
        changed={**registered,'holdout_manifest_sha256':'different'}
        changed.pop('receipt_sha256');changed=evaluation.seal(changed)
        with self.assertRaises(ValueError):
            self.run_case(hold,mode='holdout',registration=changed,development_path=dev,worker_factory=Worker)
        self.assertEqual(Worker.calls,[])

    def test_holdout_rerun_with_another_output_filename_is_rejected(self):
        dev,hold,registered=self.holdout()
        self.run_case(hold,mode='holdout',registration=registered,development_path=dev,worker_factory=Worker)
        factory=Mock()
        with self.assertRaisesRegex(ValueError,'already exposed'):
            self.run_case(hold,mode='holdout',name='renamed.json',registration=registered,development_path=dev,worker_factory=factory)
        factory.assert_not_called()

    def test_failed_holdout_reservation_still_prevents_silent_rerun(self):
        dev,hold,registered=self.holdout()
        self.run_case(hold,mode='holdout',registration=registered,development_path=dev,worker_factory=Mock(side_effect=ValueError()))
        with self.assertRaisesRegex(ValueError,'already exposed'):
            self.run_case(hold,mode='holdout',name='retry.json',registration=registered,development_path=dev,worker_factory=Worker)

    def test_audio_mutation_after_preflight_never_reaches_worker(self):
        path,data=self.dataset()
        def factory(*args):
            (path.parent/data['clips'][0]['audio_path']).write_bytes(b'changed')
            return Worker()
        report=self.run_case(path,worker_factory=factory)
        self.assertEqual(report['clips'][0]['status'],'failed')
        self.assertFalse(report['clips'][0]['processing_attempted'])
        self.assertEqual(Worker.calls,[])

    def test_ledger_rejects_audio_reuse_across_renamed_corpora(self):
        ledger=runner.ExposureLedger(self.ledger)
        data={'manifest_sha256':'a','speakers':{('one','reader')},'audio_hashes':{'same-bytes'}}
        ledger.reserve('dev','development',data,self.frozen)
        data={**data,'speakers':{('renamed','other-reader')}}
        with self.assertRaisesRegex(ValueError,'audio was already exposed'):
            ledger.reserve('hold','holdout',data,self.frozen)

    def test_concurrent_holdout_reservation_allows_exactly_one_run(self):
        ledger=runner.ExposureLedger(self.ledger)
        data={'manifest_sha256':'a','speakers':{('one','reader')},'audio_hashes':{'same-bytes'}}
        def reserve(number):
            try:
                ledger.reserve(str(number),'holdout',data,self.frozen)
                return 'reserved'
            except ValueError:return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(reserve,[1,2]))
        self.assertCountEqual(outcomes,['reserved','rejected'])

    def test_network_guard_blocks_socket_and_restores_environment(self):
        previous=os.environ.get('OFFLINE_MODE')
        with runner.network_disabled():
            self.assertEqual(os.environ['OFFLINE_MODE'],'1')
            with self.assertRaises(RuntimeError):socket.getaddrinfo('example.invalid',443)
            with self.assertRaises(RuntimeError):socket.create_connection(('example.invalid',443))
        self.assertEqual(os.environ.get('OFFLINE_MODE'),previous)

    def test_timeout_terminates_worker_and_closes_pipe(self):
        class Process:
            alive=True;terminated=False
            def is_alive(self):return self.alive
            def join(self,timeout):pass
            def terminate(self):self.terminated=True;self.alive=False
        worker=runner.LocalWorker.__new__(runner.LocalWorker)
        worker.process=Process();worker.connection=Mock();worker.connection.poll.return_value=False
        with self.assertRaisesRegex(runner.ClipFailure,'WorkerTimeout'):worker._receive(.01)
        self.assertTrue(worker.process.terminated);worker.connection.close.assert_called_once()

    def test_cli_rejects_public_output_without_logging_private_paths(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/evaluate_speech.py'),'--mode','controls',
            '--freeze',str(self.root/'private-freeze.json'),'--model-dir',str(self.root/'private-model'),
            '--dataset',str(self.root/'private-manifest.json'),'--out',str(self.root/'public.json')],
            capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertNotIn(str(self.root),result.stdout+result.stderr)


if __name__=='__main__':unittest.main(verbosity=2)
