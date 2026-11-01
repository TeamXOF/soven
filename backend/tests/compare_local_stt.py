"""Controlled, offline decoding comparison on locally generated adult speech."""
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.test-deps'))
sys.path.insert(0,str(ROOT/'backend'))
OUT=ROOT/'analysis/meta-hackathon-2026/runtime-validation'
cache=Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots'
model_path=next(p for p in cache.iterdir() if (p/'model.bin').is_file())
os.environ.update(OFFLINE_MODE='1',HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
from faster_whisper import WhisperModel
LITERAL_PROMPTS={'en':'Verbatim transcription of a young child reading one sentence aloud. Transcribe exactly what is said, word for word. Do not correct grammar, do not add or remove words.'}

model=WhisperModel(str(model_path),device='cpu',compute_type='int8',local_files_only=True)
rows=[]
variants=[('vad_with_prompt',True,LITERAL_PROMPTS['en']),('vad_without_prompt',True,None),('no_vad_without_prompt',False,None)]
with patch('socket.socket.connect',side_effect=AssertionError('Network prohibited')):
    for variant,vad,prompt in variants:
        for name in ['correct','leading-insertion','missing-word','substitution','missing-ending']:
            tick=time.perf_counter()
            segments,_=model.transcribe(str(OUT/(name+'.wav')),language='en',word_timestamps=True,
                beam_size=1,temperature=0,condition_on_previous_text=False,initial_prompt=prompt,
                vad_filter=vad,vad_parameters={'min_silence_duration_ms':300,'speech_pad_ms':200} if vad else None)
            segments=list(segments)
            row={'variant':variant,'case':name,'seconds':round(time.perf_counter()-tick,3),
                 'transcript':' '.join(s.text.strip() for s in segments),
                 'words':[{'word':w.word.strip(),'start':w.start,'end':w.end,'probability':w.probability} for s in segments for w in s.words or []]}
            rows.append(row)
            print(json.dumps({k:v for k,v in row.items() if k!='words'}),flush=True)
            (OUT/'decoder-comparison.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
