"""Small, deterministic child-speech pilot from the authors' public test set.

SpeechOcean762, Zhang et al., Interspeech 2021; CC BY 4.0 per OpenSLR SLR101.
No model weights trained; one utterance per speaker aged 5–10. The first 20
speakers are exploratory development data; skip 20 for a small frozen holdout.
Reference text is a reading prompt, so target WER is NOT pure ASR accuracy.
"""
import json
import hashlib
import os
from pathlib import Path
import re
import sys
import time
import urllib.request
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.qa/runtime-validation'
DATA=OUT/'speechocean-sample';DATA.mkdir(parents=True,exist_ok=True)
BASE='https://raw.githubusercontent.com/jimbozhang/speechocean762/main/'


def fetch(relative,destination):
    if not destination.exists():
        request=urllib.request.Request(BASE+relative,headers={'User-Agent':'SpeakFlow-local-validation'})
        with urllib.request.urlopen(request,timeout=60) as response:
            destination.write_bytes(response.read())
    return destination.read_bytes()


ages={speaker.zfill(4):int(age) for speaker,age in (line.split() for line in fetch('test/spk2age',DATA/'spk2age').decode().splitlines())}
paths=dict(line.split(maxsplit=1) for line in fetch('test/wav.scp',DATA/'wav.scp').decode().splitlines())
scores=json.loads(fetch('resource/scores.json',DATA/'scores.json'))
selected=[];seen=set();eligible=0
skip=int(os.getenv('CHILD_VALIDATION_SKIP_SPEAKERS','0'))
report_name=os.getenv('CHILD_VALIDATION_REPORT','child-corpus-results.json')
if Path(report_name).name!=report_name or not report_name.endswith('.json'):
    raise ValueError('Report must be a JSON filename')
for utterance,relative in sorted(paths.items()):
    speaker=relative.split('/')[1].replace('SPEAKER','')
    if speaker in seen or not 5<=ages.get(speaker,99)<=10:continue
    annotation=scores.get(utterance) or scores.get(str(int(utterance)))
    if not annotation:continue
    seen.add(speaker)
    eligible+=1
    if eligible<=skip:continue
    destination=DATA/(utterance+'.wav')
    fetch(relative,destination)
    selected.append({'id':utterance,'speaker':speaker,'age':ages[speaker],'annotation':annotation,'file':str(destination)})
    if len(selected)>=20:break
print(json.dumps({'downloaded_child_clips':len(selected),'selection':'lowest utterance ID per distinct test speaker aged 5-10'}),flush=True)
sys.path.insert(0,str(ROOT/'.test-deps'));sys.path.insert(0,str(ROOT/'backend'))
cache=Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots'
model=next(p for p in cache.iterdir() if (p/'model.bin').is_file())
os.environ.update(OFFLINE_MODE='1',STT_MODE='local',WHISPER_MODEL=str(model),GOOGLE_API_KEYS='',GOOGLE_API_KEY='',GROQ_API_KEY='',HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
from services.stt import get_transcript
from services import acoustic


def wer(reference,hypothesis):
    tokens=lambda t:re.findall(r"[\w']+",t.lower())
    ref,hyp=tokens(reference),tokens(hypothesis);cost=list(range(len(hyp)+1))
    for i,a in enumerate(ref,1):
        row=[i]
        for j,b in enumerate(hyp,1):row.append(min(row[-1]+1,cost[j]+1,cost[j-1]+(a!=b)))
        cost=row
    return cost[-1],len(ref)


report={'source':'https://github.com/jimbozhang/speechocean762','source_license':'CC BY 4.0 per https://openslr.elda.org/101/',
        'citation':'Zhang et al. (2021), speechocean762: An Open-Source Non-native English Speech Corpus For Pronunciation Assessment, Interspeech.',
        'scope':'20 distinct test speakers, ages 5–10, Mandarin L1 reading English; no Urdu coverage or representative global sample.',
        'selection':'First utterance by ID for each distinct test speaker aged 5–10; no score-based selection.',
        'skipped_eligible_speakers':skip,
        'decoder':'cached faster-whisper-base INT8 CPU; beam=1, VAD on, no prompt',
        'evaluation_status':'Exploratory development sample' if not skip else 'Previously uninspected speakers after freezing decoder/scoring; small holdout, not global validation',
        'interpretation':'Prompt-text agreement and exploratory comparison to expert pronunciation ratings; these are different tasks.',
        'clips':[]}
confusion={'expert_error_model_flag':0,'expert_error_model_accept':0,'expert_acceptable_model_flag':0,'expert_acceptable_model_accept':0,'unmatched_word_labels':0}
with patch('socket.socket.connect',side_effect=AssertionError('No network during child-speech inference')):
    for item in selected:
        annotation=item['annotation'];target=annotation['text']
        tick=time.perf_counter()
        try:
            transcript=get_transcript(item['file'],'en')
            features=acoustic.extract_word_acoustics(item['file'],transcript.words)
            signal=acoustic.build_signal(target,transcript,features,'en',0,0,0)
            distance,reference_words=wer(target,transcript.text)
            predictions=[w for w in signal['words'] if not w.get('extra')]
            labels=annotation.get('words',[])
            for pred,label in zip(predictions,labels):
                if acoustic.tokenize(pred['word'].lower())!=acoustic.tokenize(label['text'].lower()):
                    confusion['unmatched_word_labels']+=1;continue
                expert_error=float(label['accuracy'])<=6
                key=('expert_error_' if expert_error else 'expert_acceptable_')+('model_accept' if pred['correct'] else 'model_flag')
                confusion[key]+=1
            row={'id':item['id'],'speaker':item['speaker'],'age':item['age'],'sha256':hashlib.sha256(Path(item['file']).read_bytes()).hexdigest(),'target':target,'transcript':transcript.text,
                'model_reading_accuracy':signal['accuracy'],'expert_pronunciation_accuracy_0_10':annotation.get('accuracy'),
                'prompt_edit_distance':distance,'prompt_word_count':reference_words,'seconds':round(time.perf_counter()-tick,3)}
        except Exception as error:
            row={'id':item['id'],'speaker':item['speaker'],'age':item['age'],'error':type(error).__name__+': '+str(error)}
        report['clips'].append(row)
        report['word_comparison']=confusion
        (OUT/report_name).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps({'child_clip':item['id'],'age':item['age'],'accuracy':row.get('model_reading_accuracy'),'seconds':row.get('seconds'),'error':row.get('error')}),flush=True)
valid=[r for r in report['clips'] if 'error' not in r]
report['summary']={'completed':len(valid),'failed':len(selected)-len(valid),
    'prompt_text_edit_rate':round(sum(r['prompt_edit_distance'] for r in valid)/max(1,sum(r['prompt_word_count'] for r in valid)),4),
    'expert_error_recall':round(confusion['expert_error_model_flag']/max(1,confusion['expert_error_model_flag']+confusion['expert_error_model_accept']),4),
    'expert_acceptable_false_flag_rate':round(confusion['expert_acceptable_model_flag']/max(1,confusion['expert_acceptable_model_flag']+confusion['expert_acceptable_model_accept']),4)}
(OUT/report_name).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'child_corpus_summary':report['summary'],'word_comparison':confusion}),flush=True)
