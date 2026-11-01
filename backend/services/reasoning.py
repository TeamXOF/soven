"""
Reasoning layer (roadmap Feature 3): Gemini turns structured error data into
encouraging, age-appropriate feedback — plus the multimodal hesitation judgment.
Both have defined non-LLM fallbacks (template bank / heuristic), per roadmap
Part 2.5. Fallbacks degrade the feedback *language*, never the correctness
judgment itself.
"""
import os
import json
import base64
import logging
import asyncio
from pydantic import BaseModel, ConfigDict, Field

from services.model_client import generate_json

from core.config import settings

log = logging.getLogger("speakflow.reasoning")


class CoachingFeedback(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")
    feedback_text: str = Field(min_length=1, max_length=1000)
    comprehension_question: str = Field(max_length=500)
    practice_recommendation: str | None = Field(default=None, max_length=500)
    teacher_note: str | None = Field(default=None, max_length=700)


class WordCoaching(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")
    tip: str = Field(min_length=1, max_length=500)
    syllables: list[str] = Field(default_factory=list, max_length=30)

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(_DATA, "feedback_templates.json"), encoding="utf-8") as _f:
    TEMPLATES = json.load(_f)

FEEDBACK_SYSTEM_PROMPT = """You are a warm, encouraging reading tutor for children aged 5-10.
You receive structured JSON about one sentence a child just read aloud: per-word
correctness, phoneme mismatch labels, WPM, pauses, accuracy, and engagement flags.
These are transcript comparisons, not verified pronunciation judgments. Speech
recognition can be wrong. Describe differences as words heard differently and
invite another read; never claim the child definitely mispronounced a sound.

Return ONLY valid JSON (no markdown):
{
  "feedback_text": "1-3 short, kind, specific sentences for the CHILD. Praise what went well first. If a word was wrong, name it gently and give one concrete mouth/sound tip. Never use technical labels like 'phoneme mismatch'.",
  "comprehension_question": "One simple question about what the sentence MEANS (not about reading mechanics).",
  "practice_recommendation": "One short instruction for what to practice, naming the specific word or sound. null if the read was flawless.",
  "teacher_note": "One sentence for the teacher's dashboard, plain language."
}

If the child got everything right, celebrate briefly and make practice_recommendation an
advanced challenge (a tongue-twister using the sentence's sounds) instead of null.
Write ALL child-facing text in {language_name}."""


WORD_TIP_PROMPT = """You are a friendly reading coach for a 6-9 year-old child. One word
from their reading just tripped them up. Answer in {language_name}, warm and encouraging,
in at most 2 very short sentences a child can follow. Tell them how to say the word (where
to break it, what the tricky letter sounds like) and one concrete thing to try. Never use
technical labels or mention technology or scores.
Return ONLY valid JSON (no markdown):
{"tip": "...", "syllables": ["part1", "part2"]}"""


def split_syllables(word: str) -> list:
    """Crude vowel-group splitter for read-aloud hints ("morning" → mor/ning).
    Good enough for coaching hints; Gemini corrects it when online."""
    import re
    parts = re.findall(
        r"[^aeiouy]*[aeiouy]+(?:[^aeiouy]*(?=[^aeiouy][aeiouy])|[^aeiouy]*$)",
        (word or "").lower())
    return parts or [(word or "").lower()]


async def generate_word_tip(word: str, language: str = "en",
                            mismatch: str = "", spoken: str = "") -> dict:
    """A short per-word pronunciation tip. Gemini first (short timeout), then an
    honest local template so the tooltip always shows something useful offline."""
    payload = {"word": word, "recognized_text": spoken or "", "transcript_difference": mismatch or ""}
    try:
        prompt = WORD_TIP_PROMPT.replace(
            "{language_name}", _LANGUAGE_NAMES.get(language, "English"))
        data = WordCoaching.model_validate(await _call_gemini_json(prompt, payload, 6.0)).model_dump()
        tip = str(data.get("tip") or "").strip()
        syllables = [str(s).strip() for s in (data.get("syllables") or []) if str(s).strip()]
        if tip:
            return {"tip": tip, "syllables": syllables or split_syllables(word),
                    "source": "gemini"}
    except Exception as e:
        log.warning("word tip gemini failed: %s", e)

    syllables = split_syllables(word) if language == "en" else [word]
    if mismatch and "_vs_" in mismatch:
        a, b = mismatch.split("_vs_", 1)
        tip = f'Say it slow: {" – ".join(syllables)}. Watch the “{a}” sound — it can sneak in like “{b}”.'
    else:
        tip = f'Say it slow, piece by piece: {" – ".join(syllables)}.'
    if language == "ur":
        tip = f'لفظ «{word}» آہستہ پڑھیں، پھر پورا لفظ دوبارہ پڑھیں۔'
    return {"tip": tip, "syllables": syllables, "source": "template"}

_MIME_BY_EXT = {
    ".webm": "audio/webm", ".wav": "audio/wav", ".mp4": "audio/mp4",
    ".m4a": "audio/mp4", ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
}

_LANGUAGE_NAMES = {"en": "English", "ur": "Urdu (اردو)"}

_MODEL_NOT_FOUND_MARKERS = ("not found", "is not supported", "unsupported",
                            "does not exist", "not available")


def _configure_key():
    """Compatibility helper; credentials are selected independently per request."""
    return [key.strip() for key in settings.active_gemini_key.split(",") if key.strip()]


def _extract_json(text: str) -> dict:
    start = text.find("{")
    if start != -1:
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(text[start:])
        return parsed
    return json.loads(text)


async def _call_gemini_json(system_prompt: str, payload: dict, timeout_s: float) -> dict:
    """One Gemini JSON call with a soft timeout. Raises on failure/timeout so the
    caller can fall back (roadmap Part 2.5: never block past the timeout)."""
    last_error = RuntimeError("Reasoning unavailable")
    for model in dict.fromkeys([settings.FEEDBACK_MODEL, settings.FEEDBACK_MODEL_FALLBACK]):
        try:
            return await generate_json(system_prompt, payload, model, timeout_s)
        except Exception as error:
            last_error = error
            if not settings.active_gemini_key or os.getenv("OFFLINE_MODE") == "1":
                break
    raise last_error


def _pick_template(category: str, language: str, word: str = "", phoneme: str = "") -> dict:
    lang = TEMPLATES.get(language) or TEMPLATES["en"]
    tpl = lang.get(category) or lang["phoneme"]
    out = {}
    for key in ("feedback_text", "comprehension_question", "practice_recommendation",
                "teacher_note"):
        val = tpl.get(key)
        if isinstance(val, str):
            val = val.replace("{word}", word or "this word").replace(
                "{phoneme}", phoneme or "the sound")
        out[key] = val
    return out


def classify_category(signal: dict) -> str:
    if signal["accuracy"] >= 98:
        return "all_correct"
    if signal["hesitations"] and len(signal["hesitations"]) >= 3:
        return "hesitant"
    if signal["wpm"] and signal["wpm"] < 40:
        return "fluency"
    if any(w["phoneme_mismatch"] for w in signal["words"] if not w["correct"]):
        return "phoneme"
    if signal["accuracy"] >= 80:
        return "strong"
    return "phoneme"


async def generate_feedback(signal: dict, checkpoint_hint: dict) -> dict:
    """Phase-2 feedback. Tries Gemini; falls back to the template bank.
    Returns the Phase-2 payload dict (without phase/session fields)."""
    category = classify_category(signal)
    language = checkpoint_hint.get("language", "en")
    first_bad = next((w for w in signal["words"] if not w["correct"]), None)
    word = first_bad["word"] if first_bad else ""
    phoneme = (first_bad or {}).get("phoneme_mismatch") or ""

    payload = {
        "target_text": checkpoint_hint.get("target_text", ""),
        "comprehension_hint": checkpoint_hint.get("comprehension_hint", ""),
        "transcript": signal["transcript"],
        "words": [{"word": w["word"], "correct": w["correct"],
                   "phoneme_mismatch": w["phoneme_mismatch"]} for w in signal["words"]],
        "accuracy": signal["accuracy"],
        "wpm": signal["wpm"],
        "pauses": signal["hesitations"],
        "engagement_flag": signal.get("engagement_state", "unknown"),
    }

    try:
        prompt = FEEDBACK_SYSTEM_PROMPT.replace(
            "{language_name}", _LANGUAGE_NAMES.get(language, "English"))
        data = CoachingFeedback.model_validate(await _call_gemini_json(prompt, payload, settings.FEEDBACK_TIMEOUT_S)).model_dump()
        if not isinstance(data.get("feedback_text"), str) or not data["feedback_text"].strip():
            raise ValueError("Feedback text is required")
        if not isinstance(data.get("comprehension_question"), str):
            raise ValueError("Comprehension question must be text")
        return {
            "feedback_text": str(data.get("feedback_text", "")).strip(),
            "comprehension_question": str(data.get("comprehension_question", "")).strip(),
            "practice_recommendation": (str(data.get("practice_recommendation")).strip()
                                        if data.get("practice_recommendation") else None),
            "teacher_note": str(data.get("teacher_note", "")).strip() or None,
            "feedback_source": "gemini",
        }
    except Exception as e:
        log.warning("gemini_fallback: %s", e)
        tpl = _pick_template(category, language, word, phoneme)
        if not tpl.get("comprehension_question"):
            tpl["comprehension_question"] = checkpoint_hint.get("comprehension_hint") or None
        if not tpl.get("practice_recommendation") and word:
            lang_fb = TEMPLATES.get(language) or TEMPLATES["en"]
            tpl["practice_recommendation"] = (lang_fb.get("practice_word_fmt",
                "Practice the word '{word}'.")).replace("{word}", word)
        tpl["feedback_source"] = "template_fallback"
        return tpl


async def judge_hesitation(audio_path: str, pause_context: dict) -> str:
    """Timing observations only. Audio is never uploaded for emotion inference."""
    return "pause_detected"
