"""Measured observations, bounded coaching and explicit fallback availability."""
import os
from services.model_client import generate_json, model_candidates
from services.acoustic import align_words, score_word, tokenize, _norm
from core.config import settings
from core.speech_capabilities import has_word_timing
from .difficulty_agent import DIFFICULTY_SYSTEM_PROMPT
from .practice_agent import PRACTICE_SYSTEM_PROMPT

_FLASH = 'gemini-3.5-flash-lite'
MODEL_FALLBACK = 'gemini-flash-lite-latest'
DIFFICULTY_SCHEMA = {'type': 'object', 'properties': {
    'category': {'type': 'string', 'enum': ['WORD_READING', 'PACING', 'MIXED', 'NO_OBVIOUS_ERROR']},
    'primary_issue': {'type': 'string'}, 'secondary_issue': {'type': ['string', 'null']},
    'reasoning': {'type': 'string'}},
    'required': ['category', 'primary_issue', 'secondary_issue', 'reasoning'], 'additionalProperties': False}
PRACTICE_SCHEMA = {'type': 'object', 'properties': {'sentences': {'type': 'array', 'minItems': 1,
    'maxItems': 5, 'items': {'type': 'object', 'properties': {
        'text': {'type': 'string'}, 'target_word': {'type': 'string'},
        'difficulty': {'type': 'string', 'enum': ['easy', 'medium', 'hard']}},
        'required': ['text', 'target_word', 'difficulty'], 'additionalProperties': False}}},
    'required': ['sentences'], 'additionalProperties': False}


def _resolve_model():
    model = (os.getenv('GEN1_AGENT_MODEL', 'auto') or 'auto').strip()
    return _FLASH if model.lower() in ('', 'auto') else model


async def call_agent(system_prompt: str, user_data: dict) -> dict:
    for model in model_candidates(_resolve_model(), MODEL_FALLBACK):
        try:
            schema = DIFFICULTY_SCHEMA if system_prompt == DIFFICULTY_SYSTEM_PROMPT else PRACTICE_SCHEMA
            return await generate_json(system_prompt, user_data, model, timeout=8, schema=schema)
        except Exception:
            if not settings.active_gemini_key or os.getenv('OFFLINE_MODE') == '1':
                break
    return {'error': 'Reasoning unavailable; use measured results and template coaching.'}


def _in_language(text, language):
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1000:
        return False
    letters = [c for c in text if c.isalpha()]
    count = sum('\u0600' <= c <= '\u06ff' for c in letters) if language == 'ur' else sum(c.isascii() for c in letters)
    return bool(letters) and count / len(letters) >= .6


def _sentence_key(text):
    return tuple(_norm(w) for w in tokenize(text))


def progress_comparison(signal, history):
    language = signal.get('language', 'en')
    ur = language == 'ur'
    matches = [s for s in history if not s.get('is_mock') and s.get('accuracy') is not None
               and (s.get('language') or 'en') == language
               and _sentence_key(s.get('target_sentence', '')) == _sentence_key(signal.get('target_sentence', ''))]
    matches.sort(key=lambda s: s.get('timestamp', ''), reverse=True)
    result = {'source': 'measured_history', 'status': 'unavailable', 'trend': 'insufficient_data',
              'improvement_percentage': None, 'highlights': [], 'areas_to_watch': [],
              'comparable_attempt_count': len(matches) + 1, 'accuracy_change_points': None,
              'current_accuracy': signal['accuracy'], 'previous_accuracy': None,
              'recommendation': 'یہی جملہ دوبارہ پڑھیں۔' if ur else 'Read this sentence again for a comparison.',
              'report_text': 'موازنہ کرنے کے لیے اسی زبان میں یہی جملہ دوبارہ پڑھیں۔' if ur else
                  'Read this same sentence again in this language to compare word match.'}
    if matches:
        previous = round(float(matches[0]['accuracy']) * 100)
        current = signal['accuracy']
        delta = current - previous
        text = (f'اسی جملے کا لفظی موازنہ: اب {current}٪، پچھلی بار {previous}٪۔ فرق: {delta:+} فیصد پوائنٹس۔' if ur else
                f'Word match on this sentence: {current}% now, {previous}% previously ({delta:+} percentage points).')
        result.update(status='available', previous_accuracy=previous, accuracy_change_points=delta,
                      trend='improving' if delta > 0 else 'declining' if delta < 0 else 'stable',
                      report_text=text, highlights=[text])
    return result


def _fallback_sentences(words, signal, tier):
    # Short word practice remains achievable even when the original sentence is hard.
    language = signal.get('language', 'en')
    if words:
        return [{'text': w + ('۔' if language == 'ur' else '.'), 'target_word': w,
                 'target_phoneme': w, 'difficulty': tier} for w in words[:5]]
    text = signal.get('target_sentence', '')
    first = next(iter(tokenize(text)), '')
    return [{'text': text, 'target_word': first, 'target_phoneme': first, 'difficulty': tier}]


async def run_pipeline(signal_data: dict, session_history: list) -> dict:
    language = signal_data.get('language', 'en')
    ur = language == 'ur'
    scored = signal_data.get('word_results')
    if scored is None:
        entries = align_words(signal_data.get('target_sentence', ''), signal_data.get('words_spoken', []))
        scored = [score_word(e, {}) for e in entries if e['target']]
        scored.extend({'word': w, 'spoken': w, 'correct': False, 'extra': True, 'phoneme_mismatch': 'extra word'}
                      for e in entries for w in e.get('extra_words', []))
    target_count = len(tokenize(signal_data.get('target_sentence', '')))
    accuracy = round(100 * sum(bool(w['correct']) for w in scored) /
                     max(1, target_count + sum(bool(w.get('extra')) for w in scored)))
    signal_data = {**signal_data, 'accuracy': accuracy}
    bad = list(dict.fromkeys(w['word'] for w in scored if not w['correct'] and not w.get('extra')))
    phonetic = {'struggling_words': bad, 'struggling_phonemes': [], 'confidence': None,
                'severity': 'practice_recommended' if bad else 'none', 'source': 'measured_alignment',
                'status': 'available', 'word_observations': [w for w in scored if not w['correct']],
                'reasoning': 'یہ نتیجہ جملے اور پہچانے گئے الفاظ کا موازنہ ہے۔' if ur else
                    'These observations compare the sentence with the recognized words.'}
    difficulty = await call_agent(DIFFICULTY_SYSTEM_PROMPT, {
        **signal_data, 'phonetic_result': phonetic, 'output_language': 'Urdu (اردو)' if ur else 'English'})
    if (difficulty.get('category') not in {'WORD_READING', 'PACING', 'MIXED', 'NO_OBVIOUS_ERROR'}
            or not _in_language(difficulty.get('primary_issue'), language)):
        difficulty = {'category': 'WORD_READING' if bad else 'NO_OBVIOUS_ERROR',
                      'primary_issue': ('دکھائے گئے الفاظ آہستہ پڑھیں، پھر جملہ دوبارہ پڑھیں۔' if bad else 'اب یہی جملہ ایک بار پھر پڑھیں۔') if ur else
                          ('Read the words to review slowly, then try the sentence again.' if bad else 'Try reading the sentence once more.'),
                      'secondary_issue': None, 'reasoning': phonetic['reasoning'],
                      'source': 'template_fallback', 'status': 'fallback'}
    else:
        difficulty.update(source='model', status='available',
                          provider=getattr(difficulty, 'provider', 'unknown'), model=getattr(difficulty, 'model', None))
    pause_count = signal_data.get('pause_count', len(signal_data.get('pauses') or []))
    engagement = {'emotional_state': 'not_assessed', 'frustration_signal': None, 'engagement_level': None,
                  'suggested_tone': 'encouraging', 'source': 'measured_alignment', 'status': 'available',
                  'teacher_note': f'ریکارڈنگ میں لمبے وقفے: {pause_count}۔' if ur else f'Long gaps detected in the recording: {pause_count}.'}
    timed_words = signal_data.get('words_spoken') or []
    if (len(timed_words)<2 or any(not has_word_timing(w) for w in timed_words)
            or signal_data.get('speech_evidence',{}).get('pause_assessment')=='unavailable'):
        engagement.update(status='unavailable', source='not_assessed',
                          teacher_note='اس ریکارڈنگ میں وقفوں کا قابل اعتماد موازنہ دستیاب نہیں ہے۔' if ur else
                              'Reliable word timing is unavailable, so pauses cannot be assessed for this recording.')
    tier = 'easy' if accuracy < 70 else 'medium' if accuracy < 90 else 'hard'
    practice = await call_agent(PRACTICE_SYSTEM_PROMPT, {
        'struggling_words': bad, 'current_accuracy': accuracy, 'required_difficulty': tier,
        'grade': signal_data.get('grade', 3), 'output_language': 'Urdu (اردو)' if ur else 'English',
        'target_sentence': signal_data.get('target_sentence', ''), 'recent_sessions': session_history[:3]})
    candidates = practice.get('sentences')
    valid = isinstance(candidates, list) and 1 <= len(candidates) <= 5
    cleaned = []
    for item in candidates if valid else []:
        if not isinstance(item, dict):
            valid = False
            break
        text, word = item.get('text'), item.get('target_word')
        if (not _in_language(text, language) or len(text) > 500 or not isinstance(word, str)
                or not _norm(word) or len(tokenize(word)) != 1 or _norm(word) not in _sentence_key(text)
                or (bad and _norm(word) not in {_norm(w) for w in bad})
                or (not bad and _norm(word) not in _sentence_key(signal_data.get('target_sentence', '')))
                or item.get('difficulty') != tier
                or len(tokenize(text)) > {'easy': 8, 'medium': 12, 'hard': 18}[tier]):
            valid = False
            break
        cleaned.append({**item, 'target_phoneme': word})
    if not valid:
        practice = {'sentences': _fallback_sentences(bad, signal_data, tier),
                    'source': 'template_fallback', 'status': 'fallback'}
    else:
        practice.update(sentences=cleaned, source='model', status='available',
                        provider=getattr(practice, 'provider', 'unknown'), model=getattr(practice, 'model', None))
    practice.update(focus_area='دوبارہ پڑھنے کی مشق' if ur else 'Read and try again', difficulty_note=tier,
                    encouraging_note='ہر لفظ آرام سے پڑھیں۔ آپ کر سکتے ہیں!' if ur else 'Take your time with each word. You can do this!')
    return {'phonetic': phonetic, 'difficulty': difficulty, 'engagement': engagement,
            'practice': practice, 'progress': progress_comparison(signal_data, session_history)}
