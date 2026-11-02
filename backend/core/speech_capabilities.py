"""Shared language routes and observed speech evidence; no inference or secrets."""
from copy import deepcopy
import json
import math
from pathlib import Path
from core.languages import require_reading_language

_POLICY=json.loads((Path(__file__).resolve().parents[2]/'shared/speech-capabilities.json').read_text(encoding='utf-8'))

def speech_policy(language):
    code=require_reading_language(language)
    if code not in _POLICY['languages']:
        raise ValueError('No speech route is configured for this language')
    return code,deepcopy(_POLICY['languages'][code])

def language_speech_inventory():
    return deepcopy(_POLICY)

def finite_number(value):
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)

def has_word_timing(word):
    start,end=word.get('start'),word.get('end')
    return (word.get('timing_source') in {None,'word'}
            and finite_number(start) and finite_number(end) and 0 <= start < end)

def observed_speech_evidence(transcript,language,total_duration=None):
    code,_=speech_policy(language)
    # Punctuation is not a spoken word and cannot make timing appear complete.
    from services.acoustic import _norm
    words=[w for w in transcript.words if _norm(w.get('word',''))]
    def valid_time(w):return has_word_timing(w) and (total_duration is None or finite_number(total_duration) and w['end'] <= total_duration)
    timed=sum(valid_time(w) for w in words)
    confidences=sum(finite_number(w.get('probability')) and 0 <= w['probability'] <= 1 for w in words)
    def availability(n):return 'available' if words and n==len(words) else 'partial' if n else 'unavailable'
    ordered=all(words[i]['start'] >= words[i-1]['end'] for i in range(1,len(words))) if words and timed==len(words) else False
    simulated=transcript.fallback_reason=='mock'
    return {'schema_version':1,'origin':'simulation' if simulated else 'recognizer','language':code,
        'provider':transcript.source,'engine':getattr(transcript,'engine','unknown'),
        'fallback_reason':transcript.fallback_reason or None,
        'word_timing':'unavailable' if simulated else availability(timed),
        'recognition_confidence':'unavailable' if simulated else availability(confidences),
        'confidence_basis':'model_token_probability_not_pronunciation',
        'word_count':len(words),'timed_word_count':0 if simulated else timed,
        'pause_assessment':'available' if not simulated and len(words)>=2 and ordered else 'unavailable',
        'quality_validated':False}

def save_speech_evidence(conn,kind,record_id,evidence):
    conn.execute('INSERT OR REPLACE INTO speech_evidence(record_kind,record_id,payload_json) VALUES (?,?,?)',
                 (kind,record_id,json.dumps(evidence,allow_nan=False)))

def load_speech_evidence(conn,kind,record_id):
    row=conn.execute('SELECT payload_json FROM speech_evidence WHERE record_kind=? AND record_id=?',(kind,record_id)).fetchone()
    return json.loads(row[0]) if row else None
