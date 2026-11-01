"""Offline contracts for speech freezing; synthetic manifests, no speech inference."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from core import speech_evaluation as evaluation


class SpeechEvaluationContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = evaluation.load_profile()
        self.synthetic_profile = deepcopy(self.profile)
        model = self.root / 'model'
        model.mkdir()
        for name in ['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.txt']:
            (model / name).write_bytes(('synthetic-' + name).encode())
        self.synthetic_profile['model_artifact_sha256'] = {
            f.name: evaluation.file_hash(f) for f in model.iterdir()}
        self.model = model
        self.freeze = evaluation.freeze_baseline(model, self.synthetic_profile,
                                                 self.profile['required_versions'])
        # Dataset/receipt behavior is independent of a real downloaded model.
        self.verify = patch.object(evaluation, 'verify_freeze')
        self.verify.start()
        self.addCleanup(self.verify.stop)

    def dataset(self, name, split, speaker='reader1', corpus='synthetic', content=None):
        folder = self.root / name
        folder.mkdir(exist_ok=True)
        audio = folder / 'clip.wav'
        audio.write_bytes(content or ('synthetic-audio-' + name).encode())
        row = {'id': 'clip1', 'speaker_id': speaker, 'language': 'en',
               'age_band': 'child', 'device': 'phone', 'noise': 'quiet',
               'audio_path': 'clip.wav', 'audio_sha256': evaluation.file_hash(audio),
               'target_text': 'The cat sat.', 'reference_text': 'The dog sat.',
               'reference_kind': 'verbatim', 'reference_review': 'adjudicated',
               'target_word_matches': [True, False, True]}
        data = {'schema_version': 1, 'corpus_id': corpus, 'split': split,
                'rights_basis': 'Synthetic unit fixture; not learner audio', 'clips': [row]}
        path = folder / 'manifest.json'
        self.save(path, data)
        return path, data

    def save(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def register(self, dev, holdout):
        return evaluation.register_evaluation(dev, holdout, self.freeze)

    def test_profile_freezes_language_targets_without_enabling_spanish(self):
        self.assertEqual(self.profile['language_criteria']['en']['max_corpus_wer'], .15)
        self.assertEqual(self.profile['language_criteria']['ur']['max_corpus_wer'], .20)
        self.assertFalse(self.profile['language_criteria']['es']['runtime_enabled'])
        options = self.profile['transcribe_options']
        self.assertIsNone(options['initial_prompt'])
        self.assertIsNone(options['hotwords'])
        self.assertNotIn('language', options)
        self.assertFalse(options['condition_on_previous_text'])

    def test_profile_keeps_current_explicit_decoder_controls(self):
        tree = ast.parse((ROOT / 'backend/services/stt.py').read_text(encoding='utf-8'))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == 'transcribe'
                 and any(k.arg == 'vad_filter' for k in node.keywords)]
        self.assertEqual(len(calls), 1)
        for keyword in calls[0].keywords:
            if keyword.arg == 'language':
                continue
            self.assertEqual(self.profile['transcribe_options'][keyword.arg], ast.literal_eval(keyword.value))

    def test_freeze_records_artifacts_and_sources_without_inference(self):
        evaluation.verify_seal(self.freeze)
        self.assertFalse(self.freeze['inference_performed'])
        self.assertFalse(self.freeze['quality_validated'])
        self.assertNotIn(str(self.root), json.dumps(self.freeze))
        self.assertEqual(set(self.freeze['model_artifacts']), {'model.bin','config.json','tokenizer.json','vocabulary.txt'})
        self.assertIn('backend/services/acoustic.py', self.freeze['source_sha256'])

    def test_changed_or_missing_cached_weights_are_rejected(self):
        (self.model / 'model.bin').write_bytes(b'different-weights')
        with self.assertRaisesRegex(ValueError, 'artifacts differ'):
            evaluation.freeze_baseline(self.model, self.synthetic_profile, self.profile['required_versions'])
        (self.model / 'model.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'artifact is missing'):
            evaluation.freeze_baseline(self.model, self.synthetic_profile, self.profile['required_versions'])

    def test_dependency_drift_is_not_silent(self):
        versions = {**self.profile['required_versions'], 'av': 'wrong-version'}
        with self.assertRaisesRegex(ValueError, 'versions differ'):
            evaluation.freeze_baseline(self.model, self.synthetic_profile, versions)

    def test_receipt_tampering_and_source_drift_are_rejected(self):
        changed = deepcopy(self.freeze)
        changed['quality_validated'] = True
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            evaluation.verify_seal(changed)
        self.verify.stop()
        with patch.object(evaluation, 'load_profile', return_value=self.synthetic_profile), patch.object(
                evaluation, 'installed_versions', return_value=self.profile['required_versions']):
            evaluation.verify_freeze(self.freeze)
            with patch.object(evaluation, 'file_hash', return_value='source-drift'):
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    evaluation.verify_freeze(self.freeze)
        self.verify.start()

    def test_valid_manifest_keeps_verbatim_reference_separate_from_target(self):
        path, data = self.dataset('hold', 'holdout')
        result = evaluation.validate_dataset(path, 'holdout', self.profile)
        self.assertNotEqual(result['rows'][0]['target_text'], result['rows'][0]['reference_text'])
        self.assertEqual(result['speakers'], {('synthetic', 'reader1')})

    def test_printed_prompt_and_unreviewed_references_are_rejected(self):
        path, data = self.dataset('hold', 'holdout')
        for key, value in [('reference_kind', 'printed_prompt'), ('reference_review','unreviewed'),
                           ('reference_text', ''), ('target_text', '')]:
            variant = deepcopy(data)
            variant['clips'][0][key] = value
            self.save(path, variant)
            with self.subTest(key=key), self.assertRaises(ValueError):
                evaluation.validate_dataset(path, 'holdout', self.profile)

    def test_word_labels_require_exact_boolean_target_positions(self):
        path, data = self.dataset('hold', 'holdout')
        for labels in [None, [], [1,0,1], [True,False], ['yes'] * 3]:
            data['clips'][0]['target_word_matches'] = labels
            self.save(path, data)
            with self.assertRaisesRegex(ValueError, 'Each target word'):
                evaluation.validate_dataset(path, 'holdout', self.profile)

    def test_speaker_split_leakage_is_rejected(self):
        dev, _ = self.dataset('dev', 'development', 'same-reader')
        hold, _ = self.dataset('hold', 'holdout', 'same-reader')
        with self.assertRaisesRegex(ValueError, 'speakers overlap'):
            self.register(dev, hold)

    def test_historical_exposed_speaker_is_not_fresh_holdout(self):
        registry = json.loads(evaluation.REGISTRY.read_text(encoding='utf-8'))
        corpus = registry['corpora'][0]
        dev, _ = self.dataset('dev', 'development', 'new-dev')
        hold, _ = self.dataset('hold', 'holdout', corpus['speaker_ids'][0], corpus['corpus_id'])
        with self.assertRaisesRegex(ValueError, 'speakers overlap'):
            self.register(dev, hold)
        self.assertEqual(len(corpus['speaker_ids']), 40)

    def test_audio_leakage_is_rejected_across_different_corpus_names(self):
        dev, _ = self.dataset('dev', 'development', 'dev-reader', 'one', b'same-private-audio')
        hold, _ = self.dataset('hold', 'holdout', 'new-reader', 'two', b'same-private-audio')
        with self.assertRaisesRegex(ValueError, 'audio overlaps'):
            self.register(dev, hold)

    def test_duplicate_clips_hash_changes_and_path_escape_fail(self):
        path, data = self.dataset('hold', 'holdout')
        variants = []
        duplicate = deepcopy(data)
        duplicate['clips'].append({**duplicate['clips'][0], 'id': 'clip2'})
        variants.append(duplicate)
        changed = deepcopy(data); changed['clips'][0]['audio_sha256'] = 'wrong'; variants.append(changed)
        outside = self.root / 'outside.wav'; outside.write_bytes(b'outside')
        escaped = deepcopy(data); escaped['clips'][0]['audio_path'] = '../outside.wav'; variants.append(escaped)
        for variant in variants:
            self.save(path, variant)
            with self.assertRaises(ValueError):
                evaluation.validate_dataset(path, 'holdout', self.profile)

    def test_missing_rights_cohorts_and_false_age_changes_fail(self):
        path, data = self.dataset('hold', 'holdout')
        for key, value in [('rights_basis',''), ('split','development')]:
            variant=deepcopy(data); variant[key]=value; self.save(path,variant)
            with self.assertRaises(ValueError):evaluation.validate_dataset(path,'holdout',self.profile)
        for key in ['age_band','device','noise']:
            variant=deepcopy(data);variant['clips'][0].pop(key);self.save(path,variant)
            with self.assertRaises(ValueError):evaluation.validate_dataset(path,'holdout',self.profile)
        other=path.parent/'second.wav';other.write_bytes(b'second-audio')
        data['clips'].append({**data['clips'][0],'id':'second','age_band':'adult',
            'audio_path':'second.wav','audio_sha256':evaluation.file_hash(other)})
        self.save(path,data)
        with self.assertRaisesRegex(ValueError,'change age cohort'):
            evaluation.validate_dataset(path,'holdout',self.profile)

    def test_registration_records_gaps_and_never_claims_quality(self):
        dev,_=self.dataset('dev','development','dev-reader')
        hold,_=self.dataset('hold','holdout','new-reader')
        result=self.register(dev,hold)
        evaluation.verify_seal(result)
        self.assertFalse(result['inference_performed'])
        self.assertFalse(result['quality_validated'])
        self.assertFalse(result['coverage']['en']['release_sample_eligible'])
        self.assertIn('reference_words',result['coverage']['en']['coverage_gaps'])
        self.assertNotIn('The dog sat',json.dumps(result))

    def test_sample_eligibility_requires_balance_and_per_speaker_repeats(self):
        rows=[]
        for speaker in range(30):
            for take in range(3):
                rows.append({'speaker_id':str(speaker),'language':'en','age_band':'child' if speaker<15 else 'adult',
                    'device':'phone' if speaker<15 else 'desktop','noise':'quiet' if speaker<15 else 'background',
                    'reference_text':' '.join('word'+str(i) for i in range(20)),
                    'target_word_matches':[True]*19+[False]})
        report=evaluation.coverage({'rows':rows},self.profile)['en']
        self.assertTrue(report['release_sample_eligible'])
        rows[0]['speaker_id']='29'
        report=evaluation.coverage({'rows':rows},self.profile)['en']
        self.assertFalse(report['release_sample_eligible'])
        self.assertIn('clips_per_speaker',report['coverage_gaps'])

    def test_nonobject_and_oversize_private_manifests_fail_cleanly(self):
        path, data = self.dataset('hold', 'holdout')
        for value in [[], {**data, 'clips': ['private-invalid-clip']}]:
            self.save(path, value)
            with self.assertRaises(ValueError):
                evaluation.validate_dataset(path, 'holdout', self.profile)
        path.write_bytes(b' ' * (8 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'size limit'):
            evaluation.validate_dataset(path, 'holdout', self.profile)

    def test_unexpected_model_assets_require_a_new_freeze(self):
        (self.model / 'preprocessor_config.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'artifacts differ'):
            evaluation.freeze_baseline(self.model, self.synthetic_profile, self.profile['required_versions'])

    def test_receipts_are_exclusive_and_cannot_overwrite_prior_registration(self):
        path=self.root/'receipt.json'
        evaluation.write_new_receipt(path,{'inference_performed':False})
        with self.assertRaises(FileExistsError):
            evaluation.write_new_receipt(path,{'changed':True})
        self.assertFalse(json.loads(path.read_text())['inference_performed'])

    def test_cli_check_has_no_weights_network_or_private_output(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/freeze_speech_evaluation.py'),'check'],
            capture_output=True,text=True,env={**os.environ,'OFFLINE_MODE':'1','HF_HUB_OFFLINE':'1'})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(result.stdout)['inference_performed'])
        result=subprocess.run([sys.executable,str(ROOT/'tools/freeze_speech_evaluation.py'),'freeze',
            '--model-dir',str(self.model),'--out',str(self.root/'public.json')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertFalse((self.root/'public.json').exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
