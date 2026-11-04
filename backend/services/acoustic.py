"""
Acoustic evidence + comparison/scoring engine (roadmap Features 1 & Part 2.1).

Reading accuracy measures agreement between target text and the transcript.
Recognition confidence and acoustic features remain separate observations:
neither establishes whether a child pronounced a word correctly.
"""
import os
import re
import json
import logging
import unicodedata

from core.config import settings
from core.speech_capabilities import has_word_timing, finite_number, observed_speech_evidence

log = logging.getLogger("speakflow.acoustic")

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(_DATA, "phoneme_confusions.json"), encoding="utf-8") as _f:
    CONFUSION_PAIRS = json.load(_f)

def tokenize(text: str) -> list:
    """Unicode words, including combining marks, without punctuation tokens."""
    tokens, current = [], []
    for ch in unicodedata.normalize('NFC', text or '').replace('’', "'"):
        if unicodedata.category(ch)[0] in {'L', 'N', 'M'} or (ch == "'" and current):
            current.append(ch)
        elif current:
            token = ''.join(current).strip("'")
            if token:
                tokens.append(token)
            current = []
    if current:
        token = ''.join(current).strip("'")
        if token:
            tokens.append(token)
    return tokens


def _norm(word: str) -> str:
    return ''.join(tokenize(word.casefold()))


# Common English inflection endings — a child reading "jump" for "jumped" or
# "sleep" for "sleeping" made a real reading error (skipped the ending) and the
# assessment must say so instead of calling it a generic mispronunciation.
_EN_ENDINGS = ("'s", "s", "es", "ed", "d", "ing", "n", "ning")


def _morphology_error(target: str, spoken: str):
    """Detect a missing/added inflection ending between the printed word and
    what was actually said. Returns (kind, suffix) or None. Latin-suffix based,
    so it is naturally a no-op for Urdu."""
    t, s = _norm(target), _norm(spoken)
    if not t or not s or t == s:
        return None
    if t.startswith(s):
        # printed word carries the ending the child did not say
        rest = t[len(s):]
        if rest in _EN_ENDINGS and len(s) >= 3:
            return ("missing", rest)
    if s.startswith(t):
        # child said an ending that is not printed
        rest = s[len(t):]
        if rest in _EN_ENDINGS and len(t) >= 3:
            return ("added", rest)
    return None


def align_words(target_text: str, spoken_words: list) -> list:
    """Align spoken words onto target words.
    Returns one entry per TARGET word:
      {target, spoken, matched, probability, extra_after}
    `extra_after` counts spoken words inserted right after this target word
    (stutters/repeats), which feed hesitation analysis.
    """
    import difflib
    targets = tokenize(target_text)
    spoken = [(w["word"], w) for w in spoken_words if _norm(w["word"])]
    s_words = [_norm(w) for w, _ in spoken]
    t_words = [_norm(t) for t in targets]

    matcher = difflib.SequenceMatcher(None, t_words, s_words, autojunk=False)
    entries = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        pairs = min(i2 - i1, j2 - j1)
        for k in range(pairs):
            t_idx, s_idx = i1 + k, j1 + k
            _, meta = spoken[s_idx]
            if t_words[t_idx] == s_words[s_idx]:
                matched, morph = True, None
            else:
                # "sleep" for "sleeping" / "jump" for "jumped": a word-ending
                # error, not a random mismatch — keep it visible to the scorer
                morph = _morphology_error(targets[t_idx], spoken[s_idx][0])
                matched = morph is not None
            entries.append({
                "target": targets[t_idx],
                "spoken": spoken[s_idx][0],
                "matched": matched,
                "morphology": morph,
                "probability": meta.get("probability"),
                "extra_after": 0,
                "spoken_meta": meta,
            })
        # Remaining targets with no spoken counterpart (skipped words)
        for ti in range(i1 + pairs, i2):
            entries.append({
                "target": targets[ti], "spoken": None, "matched": False,
                "morphology": None,
                "probability": 0.0, "extra_after": 0, "spoken_meta": None,
            })
        # Extra spoken words (stutters/insertions/ad-libbed words) attach to the
        # previous entry — their texts feed the scorer so inserted words count
        # as reading errors instead of disappearing
        extra_texts = [spoken[j1 + pairs + k][0] for k in range((j2 - j1) - pairs)]
        if extra_texts and not entries:
            entries.append({"target": "", "spoken": None, "matched": False,
                            "morphology": None, "probability": None,
                            "extra_after": 0, "spoken_meta": None})
        if extra_texts and entries:
            entries[-1]["extra_after"] += len(extra_texts)
            entries[-1].setdefault("extra_words", []).extend(extra_texts)
    return entries


def _guess_phoneme_mismatch(target: str, spoken: str, language: str):
    """A transcript substitution is not proof of a sound-level confusion."""
    return "word substitution" if target and spoken and _norm(target) != _norm(spoken) else None


def _formants(seg, sr: int) -> dict:
    """F1/F2 formant estimate via LPC root-solving (standard rule: order ≈ 2 + sr/1000).
    Returns zeros when the segment is too short or solving fails — zeros are
    treated as 'no evidence' downstream, never as maximum disagreement."""
    out = {"f1": 0.0, "f2": 0.0}
    try:
        import numpy as np
        import librosa
        frame = int(sr * 0.025)
        if seg.size < frame:
            return out
        x = seg[:frame * ((seg.size // frame))]  # trim to whole frames
        x = np.append(x[0], x[1:] - 0.97 * x[:-1])  # pre-emphasis
        a = librosa.lpc(x.astype(np.float32), order=2 + sr // 1000)
        roots = np.roots(a)
        roots = [r for r in roots if np.imag(r) > 0.01]
        freqs = sorted((np.angle(r) * (sr / (2 * np.pi))).real for r in roots)
        band = [f for f in freqs if 150.0 < f < 4500.0]
        if band:
            out["f1"] = round(float(band[0]), 1)
        if len(band) > 1:
            out["f2"] = round(float(band[1]), 1)
    except Exception as e:
        log.debug("formant estimation failed: %s", e)
    return out


def extract_word_acoustics(audio_path: str, spoken_words: list) -> dict:
    """Per-word acoustic features via librosa with resilient numpy/ffmpeg fallback.
    Pitch analysis runs ONCE over just the speech region (or full clip when words are empty),
    keeping the Phase-1 acoustic budget small while guaranteeing reliable calculation."""
    import numpy as np

    y = None
    sr = 16000
    has_librosa = False
    try:
        import librosa
        has_librosa = True
        y, sr = librosa.load(audio_path, sr=16000, mono=True, duration=121)
    except Exception:
        pass

    if y is None:
        # Fallback 1: wave module for WAV files
        try:
            import wave
            with wave.open(audio_path, "rb") as wf:
                sr = wf.getframerate()
                n = wf.getnframes()
                frames = wf.readframes(n)
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                if sampwidth == 2:
                    raw = np.frombuffer(frames, dtype=np.int16)
                    if channels > 1:
                        raw = raw[::channels]
                    y = raw.astype(np.float32) / 32768.0
        except Exception:
            pass

    if y is None:
        # Fallback 2: ffmpeg subprocess to 16kHz s16le PCM
        import subprocess
        try:
            cmd = ["ffmpeg", "-i", audio_path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
            y = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
            sr = 16000
        except Exception:
            y = np.zeros(16000, dtype=np.float32)
            sr = 16000

    total_dur = len(y) / sr if sr else 0.0
    if total_dur > 120:
        raise ValueError("Recordings must be no longer than two minutes")
    spoken_words = [w for w in spoken_words if has_word_timing(w) and w['end'] <= total_dur]

    # Pitch track once for the SPEECH REGION only (or entire clip if words are empty)
    pitch_variance = None
    f0 = None
    frame_offset = 0

    if spoken_words:
        t0 = max(0.0, float(min(w["start"] for w in spoken_words)) - 0.25)
        t1 = min(total_dur, float(max(w["end"] for w in spoken_words)) + 0.25)
        if t1 > t0:
            i0, i1 = int(t0 * sr), int(t1 * sr)
            region = y[i0:i1]
            frame_offset = i0 / 512
        else:
            region = y
    else:
        region = y

    if len(region) > 0:
        if has_librosa:
            try:
                pitch_options = {"fmin": librosa.note_to_hz("C2"), "fmax": librosa.note_to_hz("C7"),
                                 "frame_length": 1024, "hop_length": 512, "sr": sr}
                if settings.PITCH_ESTIMATOR == "pyin":
                    f0, voiced_flag, _ = librosa.pyin(region, **pitch_options)
                else:
                    f0 = librosa.yin(region, **pitch_options)
                    rms_frames = librosa.feature.rms(y=region, frame_length=1024, hop_length=512)[0]
                    voiced_flag = rms_frames[:len(f0)] > max(0.005, float(np.max(rms_frames)) * 0.05)
                    f0 = np.where(voiced_flag, f0, np.nan)
                valid_f0 = f0[voiced_flag] if (f0 is not None and voiced_flag is not None
                                               and voiced_flag.any()) else np.array([])
                pitch_variance = float(np.var(valid_f0)) if valid_f0.size else None
            except Exception:
                pass

        if f0 is None:
            # Resilient numpy autocorrelation pitch tracking
            hop = 512
            frame_len = 1024
            f0_list = []
            min_lag = max(1, int(sr / 500))
            max_lag = min(frame_len - 1, int(sr / 65))
            for idx in range(0, len(region) - frame_len, hop):
                frame = region[idx:idx + frame_len]
                rms = float(np.sqrt(np.mean(frame ** 2)))
                if rms < 0.008:
                    f0_list.append(np.nan)
                    continue
                frame_norm = frame - np.mean(frame)
                corr = np.correlate(frame_norm, frame_norm, mode='full')[len(frame_norm) - 1:]
                search = corr[min_lag:max_lag]
                if len(search) and corr[0] > 0:
                    peak = int(np.argmax(search)) + min_lag
                    if corr[peak] > 0.25 * corr[0]:
                        f0_list.append(float(sr / peak))
                    else:
                        f0_list.append(np.nan)
                else:
                    f0_list.append(np.nan)
            f0 = np.array(f0_list)
            valid_f0 = f0[~np.isnan(f0)] if f0.size else np.array([])
            pitch_variance = float(np.var(valid_f0)) if valid_f0.size else None

    frame_rate = sr / 512  # default hop
    feats = {}
    for w in spoken_words:
        start, end = float(w["start"]), max(float(w["end"]), float(w["start"]) + 0.01)
        i0, i1 = int(start * sr), min(int(end * sr), len(y))
        seg = y[i0:i1]
        if seg.size == 0:
            feats[(start, end)] = {"rms": 0.0, "zcr": 0.0, "pitch_std": 0.0,
                                   "f1": 0.0, "f2": 0.0}
            continue
        f0_seg = np.array([])
        if f0 is not None:
            fi0 = max(0, int(start * frame_rate - frame_offset))
            fi1 = max(fi0 + 1, int(end * frame_rate - frame_offset))
            f0_seg = f0[fi0:fi1]
            f0_seg = f0_seg[~np.isnan(f0_seg)] if f0_seg.size else np.array([])
        
        if has_librosa:
            try:
                zcr_val = float(np.mean(librosa.feature.zero_crossing_rate(seg))) if seg.size > 64 else 0.0
            except Exception:
                zcr_val = float(np.mean(np.abs(np.diff(np.sign(seg))) > 0)) if seg.size > 64 else 0.0
        else:
            zcr_val = float(np.mean(np.abs(np.diff(np.sign(seg))) > 0)) if seg.size > 64 else 0.0

        feats[(start, end)] = {
            "rms": float(np.sqrt(np.mean(seg ** 2))),
            "zcr": zcr_val,
            "pitch_std": float(np.std(f0_seg)) if f0_seg.size else 0.0,
            **_formants(seg, sr),
        }

    pitch_contour = []
    if f0 is not None and len(f0) > 0:
        step = max(1, len(f0) // 40)
        pitch_contour = [round(float(v), 1) if not np.isnan(v) else None for v in f0[::step]]

    loudness_series = []
    try:
        hop = 512
        frame_len = 1024
        if has_librosa:
            try:
                full_rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop)[0]
            except Exception:
                full_rms = [np.sqrt(np.mean(y[i:i + frame_len] ** 2)) for i in range(0, len(y) - frame_len, hop)]
        else:
            full_rms = [np.sqrt(np.mean(y[i:i + frame_len] ** 2)) for i in range(0, len(y) - frame_len, hop)]
        step = max(1, len(full_rms) // 40)
        loudness_series = [round(float(20 * np.log10(max(float(r), 1e-5))), 1) for r in full_rms[::step]]
    except Exception:
        pass

    return {
        "word_features": feats,
        "pitch_variance": pitch_variance,
        "pitch_contour": pitch_contour,
        "loudness_series": loudness_series,
        "total_duration": total_dur,
        "sample_rate": sr,
        "pitch_method": "librosa" if has_librosa else "autocorr",
    }


def score_word(entry: dict, acoustics: dict) -> dict:
    """Score transcript agreement without converting ASR doubt to reader errors."""
    target = entry["target"]

    if not entry["matched"]:
        # Wrong word or skipped word
        score = 20
        mismatch = _guess_phoneme_mismatch(target, entry.get("spoken") or "", entry.get("language", "en")) \
            if entry.get("spoken") else None
        return {
            "word": target or (entry.get("spoken") or ""),
            "correct": False,
            "score": score,
            "phoneme_mismatch": mismatch,
            "spoken": entry.get("spoken") or "",
        }

    raw_probability = entry.get("probability")
    prob = max(0.0, min(1.0, float(raw_probability))) if raw_probability is not None else None

    # Word-ending errors (missing/added -ed, -ing, -s…): below the pass bar,
    # with an honest label the child can act on
    morph = entry.get("morphology")
    if morph:
        kind, suf = morph
        return {
            "word": target,
            "correct": False,
            "score": 50,
            "phoneme_mismatch": f"missing -{suf}" if kind == "missing" else f"added -{suf}",
            "spoken": entry.get("spoken") or "",
        }

    return {"word": target, "correct": True, "score": 100,
            "phoneme_mismatch": None, "spoken": entry.get("spoken") or "",
            "recognition_confidence": prob, "assessment_basis": "transcript_alignment"}


def detect_hesitations(spoken_words: list) -> list:
    """Gaps > PAUSE_FLAG_MS between consecutive spoken words."""
    pauses = []
    # Never bridge over a word whose timing is missing, estimated or invalid.
    for previous,current in zip(spoken_words,spoken_words[1:]):
        if not has_word_timing(previous) or not has_word_timing(current):continue
        gap_ms=(current['start']-previous['end'])*1000
        if gap_ms > settings.PAUSE_FLAG_MS:
            pauses.append({'after_word':previous['word'],'pause_ms':int(round(gap_ms)),
                           'flagged_ambiguous':bool(gap_ms < settings.PAUSE_AMBIGUOUS_MS)})
    return pauses


def engagement_heuristic(pitch_variance: float, pauses: list, accuracy: float) -> str:
    """Describe observable reading behavior; do not infer emotions."""
    if any(p["pause_ms"] >= settings.PAUSE_AMBIGUOUS_MS for p in pauses):
        return "pauses_detected"
    return "steady_reading" if accuracy >= 85 else "practice_recommended"



def stars_for(accuracy: float) -> int:
    if accuracy >= 95: return 3
    if accuracy >= 80: return 2
    if accuracy >= settings.CHECKPOINT_PASS_THRESHOLD: return 1
    return 0


def build_signal(target_text: str, transcript_result, acoustics: dict, language: str,
                 stt_ms: float, acoustic_ms: float, scoring_ms: float) -> dict:
    """Assemble the full Phase-1 payload from transcript + features + scoring."""
    entries = align_words(target_text, transcript_result.words)
    for e in entries:
        e["language"] = language

    words_scored = [score_word(e, acoustics) for e in entries if e["target"]]

    # Inserted words that were never printed (stutters, ad-libbed words like
    # saying "Jesus" mid-sentence) are real reading errors — penalize them
    extras_scored = []
    for e in entries:
        for w in e.get("extra_words") or []:
            extras_scored.append({
                "word": w, "correct": False, "score": 15,
                "phoneme_mismatch": "extra word", "spoken": w, "extra": True,
            })
    words_scored.extend(extras_scored)

    target_count = max(len(tokenize(target_text)), 1)
    correct_count = sum(1 for w in words_scored if w["correct"])
    accuracy = int(round(correct_count / (target_count + len(extras_scored)) * 100))

    evidence=observed_speech_evidence(transcript_result,language,acoustics.get("total_duration"))
    pauses = detect_hesitations(transcript_result.words) if evidence["pause_assessment"]=="available" else []
    wpm = 0.0
    if transcript_result.words:
        dur = acoustics.get("total_duration")
        if finite_number(dur) and dur > 0:
            wpm = round(sum(bool(_norm(w['word'])) for w in transcript_result.words) / dur * 60, 1)

    acc_ratio = max(0.0, min(1.0, accuracy / 100.0))
    pause_penalty = min(20.0, len(pauses) * 1.5)
    wcpm = max(0.0, round((wpm * acc_ratio) - pause_penalty, 1))

    probs = [w.get("probability") for w in transcript_result.words if isinstance(w, dict) and w.get("probability") is not None]
    confidence = round(float(sum(probs) / len(probs)), 2) if probs else (0.90 if accuracy >= 80 else 0.75)

    pause_timeline = [
        {"start": p.get("start"), "end": p.get("end"), "duration_s": round(p.get("duration_ms", 0) / 1000.0, 2)}
        for p in pauses
    ]

    return {
        "speech_evidence":evidence,
        "transcript": transcript_result.text,
        "words": words_scored,
        "wpm": wpm,
        "wcpm": wcpm,
        "confidence": confidence,
        "pitch_contour": acoustics.get("pitch_contour", []),
        "loudness_series": acoustics.get("loudness_series", []),
        "pause_timeline": pause_timeline,
        "accuracy": accuracy,
        "passed": accuracy >= settings.CHECKPOINT_PASS_THRESHOLD,
        "stars": stars_for(accuracy),
        "hesitations": pauses,
        "pitch_variance": acoustics["pitch_variance"],
        "stt_source": transcript_result.source,
        "stt_fallback_reason": transcript_result.fallback_reason,
        "engagement_state": engagement_heuristic(
            acoustics["pitch_variance"], pauses, accuracy) if evidence["pause_assessment"]=="available" else "unknown",
        "latency_ms": {
            "stt": int(stt_ms),
            "acoustic": int(acoustic_ms),
            "scoring": int(scoring_ms),
            "total_phase1": int(stt_ms + acoustic_ms + scoring_ms),
        },
    }
