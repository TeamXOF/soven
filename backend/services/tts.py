"""
Text-to-Speech (TTS) service for SOVEN.
Provides audio synthesis for coach guidance and pronunciation modeling
in English ('en'), Urdu ('ur'), and Spanish ('es').
Supports edge-tts / cached audio files with client-side window.speechSynthesis fallback.
"""
import os
import hashlib
import logging
from pathlib import Path

log = logging.getLogger("soven.tts")

_BACKEND_DIR = Path(__file__).resolve().parents[1]
TTS_CACHE_DIR = _BACKEND_DIR / "data" / "tts_cache"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Standard voice mapping
VOICE_MAP = {
    "en": "en-US-AnaNeural",
    "ur": "ur-PK-UzmaNeural",
    "es": "es-ES-ElviraNeural",
}


def _cache_key(text: str, language: str) -> str:
    digest = hashlib.sha256(f"{language}:{text.strip()}".encode("utf-8")).hexdigest()
    return f"{language}_{digest[:16]}.mp3"


async def synthesize_speech(text: str, language: str = "en") -> Path | None:
    """
    Synthesize audio using edge-tts if available, caching result as MP3.
    Returns the file Path to the cached audio if successful, None otherwise.
    """
    text = (text or "").strip()
    if not text:
        return None

    lang = language.lower()
    if lang not in VOICE_MAP:
        lang = "en"

    cache_file = TTS_CACHE_DIR / _cache_key(text, lang)
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file

    voice = VOICE_MAP.get(lang, "en-US-AnaNeural")
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(cache_file))
        if cache_file.exists() and cache_file.stat().st_size > 0:
            return cache_file
    except ImportError:
        log.info("edge_tts not installed; relying on cached audio or browser SpeechSynthesis")
    except Exception as e:
        log.warning("edge_tts synthesis failed (%s); falling back to browser SpeechSynthesis", e)

    return None


def get_cached_audio(text: str, language: str = "en") -> Path | None:
    """Return path to existing cached MP3 if it exists."""
    lang = language.lower() if language.lower() in VOICE_MAP else "en"
    cache_file = TTS_CACHE_DIR / _cache_key(text, lang)
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file
    return None

