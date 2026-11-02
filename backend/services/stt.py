"""
Speech-to-text layer with the roadmap's two fallback wrappers.

get_transcript(audio_path, language) is the ONLY place STT source is decided:
    Groq Whisper (online)  ->  local Whisper (fallback), tagged stt_source.
Every downstream consumer reads `source` off the result — nothing else
branches on connectivity (roadmap Part 1.3 / Prompt 10).
"""
import os
import time
import socket
import logging
import threading
from dataclasses import dataclass, field
from functools import lru_cache

from core.config import settings
from core.speech_capabilities import speech_policy, has_word_timing, finite_number

log = logging.getLogger("speakflow.stt")

_probe_cache = {"ts": 0.0, "value": False}
_local_transcription_lock = threading.Lock()


class NoSpeechError(ValueError):
    """A silent/unheard recording must not become a failed reading attempt."""


def _require_speech(result):
    if not result.text.strip() or not result.words:
        raise NoSpeechError("No speech was detected. Check your microphone and try again.")
    return result


def network_available() -> bool:
    """Cheap reachability probe (DNS-level), cached with a short TTL.
    Never calls Groq/Gemini themselves (roadmap Part 1.3)."""
    if os.getenv("OFFLINE_MODE") == "1":
        return False
    now = time.monotonic()
    if now - _probe_cache["ts"] < settings.NETWORK_PROBE_TTL_S:
        return _probe_cache["value"]
    value = False
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=1.0)
        sock.close()
        value = True
    except OSError:
        value = False
    _probe_cache["ts"] = now
    _probe_cache["value"] = value
    return value


@dataclass
class TranscriptResult:
    text: str = ""
    words: list = field(default_factory=list)  # [{word, start, end, probability}]
    source: str = "local_fallback"             # "groq" | "local_fallback"
    fallback_reason: str = ""
    engine: str = "unknown"


def _normalize_words(raw_words, text=""):
    from services.acoustic import tokenize
    words=[]
    for raw in raw_words or []:
        if not isinstance(raw,dict):continue
        token=str(raw.get('word','')).strip()
        if not tokenize(token):continue
        row={'word':token,'start':None,'end':None,'probability':None,'timing_source':'unavailable'}
        if has_word_timing(raw):
            row.update(start=float(raw['start']),end=float(raw['end']),timing_source='word')
        probability=raw.get('probability')
        if finite_number(probability) and 0 <= probability <= 1:
            row['probability']=float(probability)
        words.append(row)
    if not words:
        words=[{'word':w,'start':None,'end':None,'probability':None,'timing_source':'unavailable'} for w in tokenize(text)]
    return words


@lru_cache(maxsize=1)
def _get_local_whisper():
    """Loaded once at first use, reused for the process lifetime.
    Prefers faster-whisper (INT8, ~4x faster — roadmap Phase F.1); falls back
    to openai-whisper if faster-whisper isn't installed or fails to load.
    Returns a callable: (path, language) -> {text, words}."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8",
                             local_files_only=os.getenv("OFFLINE_MODE") == "1")

        def _transcribe(path, language):
            segments, _info = model.transcribe(
                path, word_timestamps=True, language=language,
                beam_size=1, temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300, "speech_pad_ms": 200})
            words = []
            for seg in segments:
                for w in (seg.words or []):
                    words.append({
                        "word": str(w.word).strip(),
                        "start": w.start,
                        "end": w.end,
                        "probability": getattr(w,"probability",None),
                    })
                if not (seg.words or []):
                    words.extend(_normalize_words([], str(seg.text)))
            return {"text": " ".join(w["word"] for w in words).strip(), "words": words, "engine":"faster_whisper"}

        log.info("Local STT: faster-whisper '%s' (INT8)", settings.WHISPER_MODEL)
        return _transcribe
    except Exception as e:
        log.warning("faster-whisper unavailable (%s) — using openai-whisper", e)
        try:
            import whisper
        except ImportError as error:
            raise RuntimeError("Local speech recognition is unavailable. Install backend requirements and cache the Whisper model before using offline mode.") from error
        if os.getenv("OFFLINE_MODE") == "1":
            cached = os.path.join(os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "whisper", settings.WHISPER_MODEL + ".pt")
            if not os.path.isfile(settings.WHISPER_MODEL) and not os.path.isfile(cached):
                raise RuntimeError("Download the local Whisper weights before enabling offline mode")
        model = whisper.load_model(settings.WHISPER_MODEL)

        def _transcribe(path, language):
            result = model.transcribe(
                path, word_timestamps=True, language=language,
                temperature=0.0, condition_on_previous_text=False)
            words = []
            for seg in result.get("segments", []):
                if not seg.get('words'):
                    words.extend(_normalize_words([],str(seg.get('text',''))))
                for w in seg.get("words", []):
                    words.append({
                        "word": str(w["word"]).strip(),
                        "start": w.get("start"),
                        "end": w.get("end"),
                        "probability": w.get("probability"),
                    })
            return {"text": result["text"].strip(), "words": _normalize_words(words,result["text"]), "engine":"openai_whisper"}

        log.info("Local STT: openai-whisper '%s'", settings.WHISPER_MODEL)
        return _transcribe


# Whisper prompts are transcript context, not instruction messages. Instructional
# prompts leaked into recognized child speech during runtime validation. Do not
# supply either instructions or the expected reading text to the recognizer.

_MIME_BY_EXT = {
    ".webm": "audio/webm", ".wav": "audio/wav", ".mp4": "audio/mp4",
    ".m4a": "audio/mp4", ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
}


def groq_whisper(audio_path: str, language: str = "en") -> TranscriptResult:
    """Online STT via Groq. Raises on any failure — get_transcript handles fallback."""
    import requests
    ext = os.path.splitext(audio_path)[1].lower()
    mime = _MIME_BY_EXT.get(ext, "audio/webm")
    with open(audio_path, "rb") as fh:
        resp = requests.post(
            settings.GROQ_STT_URL,
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            files={"file": (os.path.basename(audio_path), fh, mime)},
            # Repeated form keys for array fields (Groq API requirement)
            data=[
                ("model", settings.GROQ_STT_MODEL),
                ("temperature", "0"),
                ("response_format", "verbose_json"),
                ("timestamp_granularities[]", "word"),
                ("timestamp_granularities[]", "segment"),
                ("language", language),
            ],
            timeout=settings.STT_TIMEOUT_S,
        )
    if not resp.ok:
        raise RuntimeError(f"Speech provider returned HTTP {resp.status_code}")
    data = resp.json()
    text=str(data.get("text", "")).strip()
    raw_words=data.get('words') or []
    if not raw_words:
        # Preserve segment text without converting segment bounds to word bounds.
        raw_words=[w for segment in data.get('segments') or []
                   for w in _normalize_words([],str(segment.get('text','')))]
    return TranscriptResult(text=text,words=_normalize_words(raw_words,text),source="groq",engine="groq_whisper")



def local_whisper(audio_path: str, language: str = "en") -> TranscriptResult:
    """Offline STT via the local model (faster-whisper INT8 if available).
    Same return shape as the Groq path."""
    with _local_transcription_lock:
        result = _get_local_whisper()(audio_path, language)
    return TranscriptResult(text=result["text"], words=_normalize_words(result["words"],result["text"]),
                            source="local_fallback",engine=result.get('engine','unknown'))


def get_transcript(audio_path: str, language: str = "en") -> TranscriptResult:
    """The single STT source decision point (roadmap Prompt 10).
    Honors the teacher's STT_MODE setting: auto (Groq when online+key),
    groq (prefer cloud, graceful local fallback), local (never call Groq)."""
    language,policy=speech_policy(language)
    mode = "local" if os.getenv("OFFLINE_MODE") == "1" else settings.stt_mode
    cloud_allowed='groq_whisper' in policy['recognition']
    local_allowed='local_whisper' in policy['recognition']
    online=network_available() if mode!='local' and cloud_allowed and settings.GROQ_API_KEY else False
    if mode != "local" and cloud_allowed and online and settings.GROQ_API_KEY:
        try:
            return _require_speech(groq_whisper(audio_path, language))
        except NoSpeechError:
            raise
        except Exception as error:
            log.warning("groq_fallback: %s", type(error).__name__)
            if not local_allowed:raise RuntimeError('No permitted recognition fallback for this language') from None
            result=local_whisper(audio_path,language)
            result.fallback_reason=f"groq: {type(error).__name__}"
            return _require_speech(result)
    if not local_allowed:raise RuntimeError('No local recognition route for this language')
    reason='forced_local' if mode=='local' else 'language_route_unavailable' if not cloud_allowed else 'no_groq_key' if not settings.GROQ_API_KEY else 'offline'
    result=local_whisper(audio_path,language)
    result.fallback_reason=reason
    return _require_speech(result)
