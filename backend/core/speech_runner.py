"""Offline evaluation with bounded workers, persistent exposure and private reports."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import multiprocessing
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import time
from unittest.mock import patch
import uuid

from core.speech_evaluation import (ROOT, REGISTRY, verify_freeze, verify_seal, freeze_baseline,
    validate_dataset, register_evaluation, coverage, seal, write_new_receipt, file_hash)
from core.speech_metrics import score_clip, summarize_run

PROTOCOL_PATH = ROOT / 'backend/data/speech_runner_protocol.json'


def load_protocol():
    return json.loads(PROTOCOL_PATH.read_text(encoding='utf-8'))


def now():
    return datetime.now(timezone.utc).isoformat()


class ClipFailure(RuntimeError):
    pass


@contextmanager
def network_disabled():
    def denied(*args, **kwargs):
        raise RuntimeError('Network is disabled during speech evaluation')
    with patch.dict(os.environ, OFFLINE_MODE='1', HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1'), \
         patch.object(socket.socket, 'connect', denied), patch.object(socket.socket, 'connect_ex', denied), \
         patch.object(socket, 'create_connection', denied), patch.object(socket, 'getaddrinfo', denied):
        yield


def _worker(connection, model_dir, profile, protocol):
    logging.disable(logging.CRITICAL)
    try:
        with network_disabled():
            tick = time.perf_counter()
            from faster_whisper import WhisperModel
            from faster_whisper.audio import decode_audio
            import numpy as np
            from services.acoustic import tokenize
            model = WhisperModel(model_dir, local_files_only=True, **profile['model_options'])
            connection.send({'kind': 'ready', 'model_load_ms': round((time.perf_counter()-tick)*1000, 3)})
            while True:
                request = connection.recv()
                if request is None:
                    break
                audio_bytes, language = request
                asr_invoked = False
                try:
                    audio = decode_audio(io.BytesIO(audio_bytes), sampling_rate=16000)
                    seconds = len(audio) / 16000
                    if (not protocol['minimum_audio_seconds'] <= seconds <= protocol['maximum_audio_seconds']
                            or not np.isfinite(audio).all()):
                        raise ClipFailure('InvalidAudioDurationOrSamples')
                    asr_invoked = True
                    segments, _ = model.transcribe(audio, language=language, **profile['transcribe_options'])
                    text, words, estimated = [], [], False
                    for segment in segments:
                        text.append(segment.text.strip())
                        if not segment.words:
                            estimated = True
                            words.extend({'word':word, 'timing_source':'unavailable'} for word in tokenize(segment.text))
                        for word in segment.words or []:
                            words.append({'word': word.word.strip(), 'start': float(word.start),
                                          'end': float(word.end), 'probability': float(word.probability)})
                    connection.send({'kind': 'result', 'text': ' '.join(text).strip(), 'words': words,
                                     'audio_seconds': seconds, 'timing_source': 'unavailable' if estimated else 'word',
                                     'asr_invoked': True})
                except Exception as error:
                    connection.send({'kind': 'clip_error', 'error_type': type(error).__name__, 'asr_invoked': asr_invoked})
    except BaseException as error:
        try: connection.send({'kind': 'worker_error', 'error_type': type(error).__name__})
        except (OSError, EOFError): pass
    finally:
        connection.close()


class LocalWorker:
    def __init__(self, model_dir, profile, protocol):
        context = multiprocessing.get_context('spawn')
        self.connection, child = context.Pipe()
        self.process = context.Process(target=_worker, args=(child, str(model_dir), profile, protocol), daemon=True)
        self.protocol = protocol
        self.process.start()
        child.close()
        reply = self._receive(protocol['worker_start_timeout_seconds'])
        if reply.get('kind') != 'ready':
            self.close()
            raise ClipFailure('WorkerInitializationFailed')
        self.model_load_ms = reply['model_load_ms']

    def _receive(self, timeout):
        if not self.connection.poll(timeout):
            self.close()
            raise ClipFailure('WorkerTimeout')
        try:
            return self.connection.recv()
        except (OSError, EOFError):
            self.close()
            raise ClipFailure('WorkerExited') from None

    def transcribe(self, audio_bytes, language):
        # The worker receives only audio bytes and language, never target/reference.
        self.connection.send((audio_bytes, language))
        reply = self._receive(self.protocol['clip_timeout_seconds'])
        if reply.get('kind') != 'result':
            raise ClipFailure('RecognitionOrDecodeFailed')
        return reply

    def close(self):
        if self.process.is_alive():
            try: self.connection.send(None)
            except (OSError, EOFError): pass
            self.process.join(timeout=.5)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=2)
        self.connection.close()


class ExposureLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=15)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, mode TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,
                    freeze_sha256 TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL,
                    finished_at TEXT);
                CREATE TABLE IF NOT EXISTS speakers (
                    run_id TEXT NOT NULL, corpus_id TEXT NOT NULL, speaker_id TEXT NOT NULL,
                    PRIMARY KEY (run_id, corpus_id, speaker_id));
                CREATE TABLE IF NOT EXISTS audio (
                    run_id TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY (run_id, sha256));
            ''')

    def reserve(self, run_id, mode, dataset, frozen):
        with closing(sqlite3.connect(self.path, timeout=15)) as connection:
            try:
                connection.execute('BEGIN IMMEDIATE')
                if mode == 'holdout':
                    for corpus_id, speaker_id in dataset['speakers']:
                        if connection.execute('SELECT 1 FROM speakers WHERE corpus_id=? AND speaker_id=? LIMIT 1',
                                              (corpus_id, speaker_id)).fetchone():
                            raise ValueError('Holdout speakers were already exposed in the local ledger')
                    for digest in dataset['audio_hashes']:
                        if connection.execute('SELECT 1 FROM audio WHERE sha256=? LIMIT 1', (digest,)).fetchone():
                            raise ValueError('Holdout audio was already exposed in the local ledger')
                connection.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,NULL)',
                    (run_id, mode, dataset['manifest_sha256'], frozen['receipt_sha256'], 'reserved', now()))
                connection.executemany('INSERT INTO speakers VALUES (?,?,?)',
                    [(run_id, corpus, speaker) for corpus, speaker in sorted(dataset['speakers'])])
                connection.executemany('INSERT INTO audio VALUES (?,?)',
                    [(run_id, digest) for digest in sorted(dataset['audio_hashes'])])
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def finish(self, run_id, status):
        with closing(sqlite3.connect(self.path, timeout=15)) as connection:
            connection.execute('UPDATE runs SET status=?,finished_at=? WHERE id=?', (status, now(), run_id))
            connection.commit()


def _write_progress(path, report):
    # Replace only the report already exclusively created by this run.
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(report, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
    os.replace(temporary, path)


def _metadata(clip):
    return {key: clip[key] for key in ['id','speaker_id','language','age_band','device','noise']}


def run_evaluation(dataset_path, mode, frozen, model_dir, output, ledger_path, *,
                   registration=None, development_path=None, worker_factory=LocalWorker, preflight_model=True, candidate_profile=None):
    if mode not in {'development','holdout','controls','historical'}:
        raise ValueError('Unknown speech evaluation mode')
    verify_freeze(frozen, profile=candidate_profile)
    profile, protocol = frozen['profile'], load_protocol()
    if preflight_model:
        # Rehash actual artifacts now; do not trust an earlier receipt alone.
        freeze_baseline(model_dir, profile)
    policy = 'controls' if mode == 'controls' else 'historical' if mode == 'historical' else 'human'
    split = 'holdout' if mode == 'holdout' else 'development'
    dataset = validate_dataset(dataset_path, split, profile, reference_policy=policy)
    if mode == 'historical':
        registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
        known = {(row['corpus_id'], speaker) for row in registry['corpora'] for speaker in row['speaker_ids']}
        if not dataset['speakers'].issubset(known):
            raise ValueError('Historical mode requires previously recorded exposed speakers')
    if mode == 'holdout':
        if not registration or not development_path:
            raise ValueError('Holdout requires preregistration and the development manifest')
        verify_seal(registration)
        current = register_evaluation(development_path, dataset_path, frozen, profile=candidate_profile)
        for key in ['kind','baseline_receipt_sha256','development_manifest_sha256','holdout_manifest_sha256',
                    'exposure_registry_sha256','holdout_speaker_keys','holdout_audio_sha256','coverage']:
            if registration.get(key) != current[key]:
                raise ValueError('Preregistered evaluation inputs changed')
    output = Path(output)
    run_id = str(uuid.uuid4())
    report = {'schema_version': 1, 'kind': 'speech_evaluation_run', 'run_id': run_id,
        'mode': mode, 'status': 'starting', 'started_at_utc': now(),
        'baseline_receipt_sha256': frozen['receipt_sha256'], 'profile_id': profile['profile_id'],
        'manifest_sha256': dataset['manifest_sha256'], 'protocol': protocol,
        'registration_sha256': registration.get('receipt_sha256') if registration else None,
        'quality_validated': False, 'model_load_ms': None, 'clips': []}
    write_new_receipt(output, report)
    ledger = ExposureLedger(ledger_path)
    try:
        ledger.reserve(run_id, mode, dataset, frozen)
    except BaseException as error:
        report.update(status='rejected', error_type=type(error).__name__, finished_at_utc=now())
        _write_progress(output, seal(report))
        raise
    worker = None
    consecutive, stop_reason = 0, None
    tick = time.perf_counter()
    report['status'] = 'running'
    try:
        try:
            worker = worker_factory(model_dir, profile, protocol)
            report['model_load_ms'] = worker.model_load_ms
        except Exception as error:
            stop_reason = 'WorkerInitializationFailed:' + type(error).__name__
        for clip in dataset['rows']:
            if stop_reason:
                row = {**_metadata(clip), 'status':'not_run', 'reason':stop_reason, 'processing_attempted':False}
            else:
                started = time.perf_counter()
                attempted = False
                try:
                    audio = (Path(dataset_path).resolve().parent / clip['audio_path']).resolve(strict=True)
                    if not audio.is_relative_to(Path(dataset_path).resolve().parent):
                        raise ValueError('Audio path changed')
                    if audio.stat().st_size > 32*1024*1024:
                        raise ValueError('Audio size changed')
                    with audio.open('rb') as stream:
                        raw = stream.read(32*1024*1024+1)
                    if len(raw) > 32*1024*1024:
                        raise ValueError('Audio size changed during read')
                    if hashlib.sha256(raw).hexdigest() != clip['audio_sha256']:
                        raise ValueError('Audio changed after registration')
                    attempted = True
                    result = worker.transcribe(raw, clip['language'])
                    row = score_clip(clip, result, mode, protocol)
                    row['processing_attempted'] = True
                    consecutive = 0
                except Exception as error:
                    row = {**_metadata(clip), 'status':'failed', 'error_type':type(error).__name__, 'processing_attempted':attempted}
                    consecutive += 1
                    if isinstance(error, ClipFailure) and str(error) in {'WorkerTimeout','WorkerExited'}:
                        stop_reason = str(error)
                    elif consecutive >= protocol['maximum_consecutive_failures']:
                        stop_reason = 'ConsecutiveFailureLimit'
                row['processing_ms'] = round((time.perf_counter()-started)*1000, 3)
            report['clips'].append(row)
            _write_progress(output, report)
    except BaseException as error:
        stop_reason = 'Interrupted:' + type(error).__name__
        for clip in dataset['rows'][len(report['clips']):]:
            report['clips'].append({**_metadata(clip),'status':'not_run','reason':stop_reason,'processing_attempted':False})
    finally:
        if worker is not None: worker.close()
    sample = coverage(dataset, profile) if mode != 'historical' else {}
    report['summary'] = summarize_run(report['clips'], mode, profile, protocol, sample)
    report.update(status='completed' if all(row['status']=='ok' for row in report['clips']) else 'completed_with_failures',
                  finished_at_utc=now(), elapsed_ms=round((time.perf_counter()-tick)*1000,3))
    report = seal(report)
    _write_progress(output, report)
    ledger.finish(run_id, report['status'])
    return report
