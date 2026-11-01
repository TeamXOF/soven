"""Speech preregistration and frozen baseline contracts. No inference or network."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'backend/data/speech_evaluation_profile.json'
REGISTRY = ROOT / 'analysis/soven/SPEECH_EXPOSURE_REGISTRY.json'
SOURCE_PATHS = ['backend/services/stt.py', 'backend/services/acoustic.py',
                'backend/core/speech_evaluation.py', 'backend/core/config.py',
                'tools/freeze_speech_evaluation.py', 'backend/requirements.txt']


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def file_hash(path, text=False):
    if text:
        return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_profile(path=PROFILE):
    profile = json.loads(Path(path).read_text(encoding='utf-8'))
    options = profile['transcribe_options']
    if (profile['schema_version'] != 1 or profile['engine'] != 'faster-whisper'
            or any(options.get(key) is not None for key in ['initial_prompt', 'prefix', 'hotwords'])
            or options.get('condition_on_previous_text') is not False
            or options.get('word_timestamps') is not True or 'language' in options):
        raise ValueError('Invalid frozen speech profile')
    return profile


def seal(value):
    return {**value, 'receipt_sha256': hashlib.sha256(canonical(value)).hexdigest()}


def verify_seal(receipt):
    value = {key: data for key, data in receipt.items() if key != 'receipt_sha256'}
    if receipt.get('receipt_sha256') != hashlib.sha256(canonical(value)).hexdigest():
        raise ValueError('Frozen receipt changed')


def installed_versions(profile):
    return {name: importlib.metadata.version(name) for name in profile['required_versions']}


def freeze_baseline(model_dir, profile=None, versions=None):
    profile = profile or load_profile()
    model_dir = Path(model_dir).resolve(strict=True)
    required = ['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.txt']
    artifacts = {}
    for name in required:
        path = model_dir / name
        if not path.is_file():
            raise ValueError('Required cached model artifact is missing: ' + name)
        artifacts[name] = {'sha256': file_hash(path), 'bytes': path.stat().st_size}
    # Include any other snapshot assets that can affect preprocessing/tokenization.
    for path in sorted(model_dir.iterdir()):
        if path.is_file() and path.name not in artifacts and not path.name.startswith('.'):
            artifacts[path.name] = {'sha256': file_hash(path), 'bytes': path.stat().st_size}
    if {name: value['sha256'] for name, value in artifacts.items()} != profile['model_artifact_sha256']:
        raise ValueError('Cached model artifacts differ from the frozen candidate')
    installed = versions if versions is not None else installed_versions(profile)
    if any(installed.get(name) != expected for name, expected in profile['required_versions'].items()):
        raise ValueError('Installed speech dependency versions differ from frozen profile')
    return seal({'schema_version': 1, 'kind': 'speech_baseline_freeze',
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'profile': profile,
        'profile_sha256': hashlib.sha256(canonical(profile)).hexdigest(),
        'model_artifacts': artifacts, 'package_versions': installed,
        'environment': {'python': platform.python_version(), 'system': platform.system(),
                        'architecture': platform.machine()},
        'source_sha256': {name: file_hash(ROOT / name, text=True) for name in SOURCE_PATHS},
        'inference_performed': False, 'quality_validated': False})


def verify_freeze(receipt):
    verify_seal(receipt)
    profile = load_profile()
    if (receipt.get('kind') != 'speech_baseline_freeze'
            or receipt.get('profile_sha256') != hashlib.sha256(canonical(profile)).hexdigest()
            or receipt.get('profile') != profile):
        raise ValueError('Frozen profile differs from current candidate')
    if receipt.get('package_versions') != profile['required_versions'] or installed_versions(profile) != profile['required_versions']:
        raise ValueError('Speech dependency versions changed after freezing')
    expected = {name: file_hash(ROOT / name, text=True) for name in SOURCE_PATHS}
    if receipt.get('source_sha256') != expected:
        raise ValueError('Recognizer, scorer or evaluation source changed after freezing')


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', value) is not None


def validate_dataset(path, split, profile):
    from services.acoustic import tokenize
    path = Path(path).resolve(strict=True)
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Dataset manifest exceeds size limit')
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if not isinstance(manifest, dict):
        raise ValueError('Dataset manifest must be an object')
    if (manifest.get('schema_version') != 1 or manifest.get('split') != split
            or not _identifier(manifest.get('corpus_id'))
            or not isinstance(manifest.get('rights_basis'), str) or not manifest['rights_basis'].strip()
            or not isinstance(manifest.get('clips'), list) or not manifest['clips']):
        raise ValueError('Dataset identity, rights basis and split are required')
    ids, hashes = set(), set()
    speakers, rows, ages = set(), [], {}
    for clip in manifest['clips']:
        if not isinstance(clip, dict):
            raise ValueError('Each dataset clip must be an object')
        if not _identifier(clip.get('id')) or not _identifier(clip.get('speaker_id')):
            raise ValueError('Use pseudonymous clip and speaker identifiers')
        if clip['id'] in ids:
            raise ValueError('Duplicate clip identifier')
        ids.add(clip['id'])
        language = clip.get('language')
        if language not in profile['language_criteria']:
            raise ValueError('Language has no preregistered evaluation criteria')
        if (clip.get('reference_kind') != 'verbatim' or clip.get('reference_review') != 'adjudicated'
                or not isinstance(clip.get('reference_text'), str)
                or not isinstance(clip.get('target_text'), str)
                or not tokenize(clip['reference_text']) or not tokenize(clip['target_text'])
                or max(len(clip['reference_text']), len(clip['target_text'])) > 5000):
            raise ValueError('Adjudicated verbatim reference and separate target are required')
        labels = clip.get('target_word_matches')
        if (not isinstance(labels, list) or len(labels) != len(tokenize(clip['target_text']))
                or not all(type(label) is bool for label in labels)):
            raise ValueError('Each target word needs an adjudicated transcript-match label')
        for dimension, values in profile['language_criteria'][language]['required_cohorts'].items():
            if clip.get(dimension) not in values:
                raise ValueError('Required cohort metadata is missing or unsupported: ' + dimension)
        if clip['speaker_id'] in ages and ages[clip['speaker_id']] != clip['age_band']:
            raise ValueError('A speaker cannot change age cohort within the dataset')
        ages[clip['speaker_id']] = clip['age_band']
        relative = clip.get('audio_path')
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError('Audio paths must be relative to the private manifest directory')
        audio = (path.parent / relative).resolve(strict=True)
        if not audio.is_relative_to(path.parent) or not audio.is_file():
            raise ValueError('Audio path escapes the private dataset directory')
        if audio.stat().st_size > 32 * 1024 * 1024:
            raise ValueError('Evaluation recording exceeds 32 MiB limit')
        digest = file_hash(audio)
        if clip.get('audio_sha256') != digest:
            raise ValueError('Audio checksum does not match registered file')
        if digest in hashes:
            raise ValueError('Duplicate audio content')
        hashes.add(digest)
        speakers.add((manifest['corpus_id'], clip['speaker_id']))
        rows.append({**clip, 'audio_sha256': digest})
    return {'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'corpus_id': manifest['corpus_id'],
            'speakers': speakers, 'audio_hashes': hashes, 'rows': rows}


def coverage(dataset, profile):
    from services.acoustic import tokenize
    reports = {}
    for language in sorted({row['language'] for row in dataset['rows']}):
        rows = [row for row in dataset['rows'] if row['language'] == language]
        criteria = profile['language_criteria'][language]
        speakers = {row['speaker_id'] for row in rows}
        counts = {'speakers': len(speakers), 'clips': len(rows),
                  'reference_words': sum(len(tokenize(row['reference_text'])) for row in rows),
                  'reference_matching_target_words': sum(sum(row['target_word_matches']) for row in rows),
                  'reference_differing_target_words': sum(sum(not v for v in row['target_word_matches']) for row in rows)}
        gaps = [key for key, value in counts.items() if value < criteria['min_' + key]]
        per_speaker = Counter(row['speaker_id'] for row in rows)
        if any(count < criteria['min_clips_per_speaker'] for count in per_speaker.values()):
            gaps.append('clips_per_speaker')
        cohorts = {}
        for dimension, values in criteria['required_cohorts'].items():
            for value in values:
                key = dimension + ':' + value
                cohorts[key] = len({row['speaker_id'] for row in rows if row[dimension] == value})
                if cohorts[key] < criteria['min_speakers_per_cohort']:
                    gaps.append(key)
        reports[language] = {'counts': counts, 'clips_per_speaker': dict(per_speaker), 'cohort_speakers': cohorts,
                             'coverage_gaps': gaps, 'release_sample_eligible': not gaps}
    return reports


def register_evaluation(development_path, holdout_path, freeze, registry_path=REGISTRY):
    verify_freeze(freeze)
    profile = freeze['profile']
    development = validate_dataset(development_path, 'development', profile)
    holdout = validate_dataset(holdout_path, 'holdout', profile)
    registry = json.loads(Path(registry_path).read_text(encoding='utf-8'))
    prior_speakers = {(row['corpus_id'], speaker) for row in registry['corpora'] for speaker in row['speaker_ids']}
    prior_hashes = {digest for row in registry['corpora'] for digest in row['audio_sha256']}
    if holdout['speakers'] & (development['speakers'] | prior_speakers):
        raise ValueError('Holdout speakers overlap development or previously exposed speakers')
    if holdout['audio_hashes'] & (development['audio_hashes'] | prior_hashes):
        raise ValueError('Holdout audio overlaps development or previously exposed audio')
    return seal({'schema_version': 1, 'kind': 'speech_evaluation_preregistration',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_receipt_sha256': freeze['receipt_sha256'],
        'development_manifest_sha256': development['manifest_sha256'],
        'holdout_manifest_sha256': holdout['manifest_sha256'],
        'exposure_registry_sha256': file_hash(registry_path, text=True),
        'holdout_speaker_keys': sorted([list(value) for value in holdout['speakers']]),
        'holdout_audio_sha256': sorted(holdout['audio_hashes']),
        'coverage': coverage(holdout, profile),
        'inference_performed': False, 'quality_validated': False,
        'purpose': 'Locks inputs before evaluation; does not prove human consent, untouched status or quality'})


def write_new_receipt(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
