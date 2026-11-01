"""Compare pitch cost and resulting word decisions on the same speech fixtures."""
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.test-deps'));sys.path.insert(0,str(ROOT/'backend'))
os.environ['OFFLINE_MODE']='1'
import librosa
import numpy as np
from services import acoustic
from services.stt import TranscriptResult
OUT=ROOT/'analysis/meta-hackathon-2026/runtime-validation'
decodings=json.loads((OUT/'decoder-comparison.json').read_text())
rows=[]


def fast_pitch(y,*,fmin,fmax,frame_length,sr,**kwargs):
    pitch=librosa.yin(y,fmin=fmin,fmax=fmax,frame_length=frame_length,hop_length=512,sr=sr)
    rms=librosa.feature.rms(y=y,frame_length=frame_length,hop_length=512)[0]
    mask=rms[:len(pitch)]>max(.005,float(np.max(rms))*.05)
    pitch=np.where(mask,pitch,np.nan)
    return pitch,mask,np.where(mask,1.,0.)


for mode in ['existing_pyin','candidate_yin']:
    for case in [r for r in decodings if r['variant']=='vad_with_prompt']:
        target='The cats jumped over the fence.' if case['case']=='missing-ending' else 'The little fox woke up early in the morning.'
        tick=time.perf_counter()
        with patch.object(acoustic.settings,'PITCH_ESTIMATOR','yin' if mode=='candidate_yin' else 'pyin'):
            features=acoustic.extract_word_acoustics(str(OUT/(case['case']+'.wav')),case['words'])
        seconds=time.perf_counter()-tick
        transcript=TranscriptResult(text=case['transcript'],words=case['words'])
        signal=acoustic.build_signal(target,transcript,features,'en',0,seconds*1000,0)
        row={'mode':mode,'case':case['case'],'seconds':round(seconds,4),'accuracy':signal['accuracy'],
             'correctness':[{'word':w['word'],'correct':w['correct']} for w in signal['words']]}
        rows.append(row);print(json.dumps(row),flush=True)
(OUT/'pitch-comparison.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
