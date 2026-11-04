from core.workload import run_audio
from core.languages import require_reading_language
from core.speech_capabilities import save_speech_evidence
import json
import uuid
import base64
import tempfile
import os
import asyncio
import random
import difflib
import time
from fastapi import APIRouter, HTTPException
from agents.orchestrator import run_pipeline
from database.schema import get_db_connection
from database.models import PipelineRunRequest

class _SimulationOnly(Exception):
    pass

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# ── Dynamic warm-up sentences for the classic dashboard ──────────────────────
SENTENCE_PROMPT = """You generate warm-up reading sentences for a child (grade 3).
Difficulty rules:
- easy: 5-8 words, simple sight words and CVC patterns, no tricky blends
- medium: 8-12 words, some blends and digraphs, everyday topics
- hard: 10-16 words, dense blends, multisyllabic words, tongue-twister flavor
When output_language is "Urdu (اردو)": write natural, correct Urdu in Nastaliq
script with grade-3 vocabulary and end every sentence with ۔
Make the sentences fresh and varied (animals, adventure, daily life, weather) —
do NOT return the usual stock sentences. Every sentence must be different.
Return ONLY valid JSON: {"sentences": ["...", "..."]} with exactly {count} sentences."""

SENTENCE_BANKS = {
    "easy": [
        "The cat sat on the big red mat.",
        "We can run to the green park.",
        "A little dog dug up a bone.",
        "The sun is up in the blue sky.",
        "She has a warm hat on her head.",
        "The frog can jump and hop far.",
        "He fed his hen some corn.",
    ],
    "medium": [
        "A quick brown fox jumps over the lazy dog.",
        "The little train went down the green hill.",
        "Mum made fresh bread for the whole family.",
        "Two black birds sat on the garden fence.",
        "The children played in the park after school.",
        "A small fish swam under the old stone bridge.",
        "The friendly bus driver waved at the kids.",
    ],
    "hard": [
        "Six sleek swans swam swiftly past the wooden dock.",
        "The brave knight fought through thick fog to reach the castle.",
        "Fresh bread from the branch bakery tastes twice as nice.",
        "Grab the bright green wrench from the third shelf of the garage.",
        "Twelve twins twisted twice around the twitching purple tree.",
        "The thoughtful thistle throve through the long dry summer.",
        "She sells shiny shells and stringy seaweed by the seashore shop.",
    ],
}



SENTENCE_BANKS_ES = {
    "easy": [
        "El gato toma leche.",
        "El sol brilla en el cielo.",
        "La manzana es roja y dulce.",
        "Los pájaros cantan en el árbol.",
        "Yo leo un libro bonito.",
        "El perro corre en el parque.",
    ],
    "medium": [
        "El pequeño zorro se despertó temprano.",
        "Los amigos caminaron hacia el pueblo verde.",
        "Después de la lluvia el jardín olía fresco.",
        "Una ardilla saltó alegre sobre la rama alta.",
        "Los niños juegan felices después de la escuela.",
        "Esta parte del cuento es muy divertida.",
    ],
    "hard": [
        "El río cristalino desciende rápido por la montaña rocosa.",
        "Las estrellas iluminan el sendero misterioso del bosque.",
        "El valiente explorador descubrió un antiguo tesoro escondido.",
        "El viento fresco soplaba entre los pinos gigantes de la colina.",
        "La pequeña lechuza observaba en silencio desde la torre.",
        "Los pájaros cantores dieron la bienvenida al nuevo amanecer.",
    ],
}

SENTENCE_BANKS_UR = {
    "easy": [
        "علی اسکول جاتا ہے۔",
        "آم میٹھا ہوتا ہے۔",
        "بلی دودھ پیتی ہے۔",
        "پرندے آسمان میں اڑتے ہیں۔",
        "چاند رات میں نظر آتا ہے۔",
        "میں کتاب پڑھتا ہوں۔",
    ],
    "medium": [
        "چھوٹا لومڑ صبح جلدی اٹھا۔",
        "دوست گاؤں کی طرف چل پڑے۔",
        "بارش کے بعد باغ بہت ہرا بھرا تھا۔",
        "ننھی چڑیا نے درخت پر گھونسلہ بنایا۔",
        "بچے میدان میں کرکٹ کھیل رہے ہیں۔",
        "کہانی کا یہ حصہ بہت دلچسپ تھا۔",
    ],
    "hard": [
        "پہاڑی سے برفانی ندی گرجتی ہوئی گزرتی ہے۔",
        "شہر کی گلیوں میں روشنیوں کی چادر بچھ جاتی ہے۔",
        "کشتکار نے تیز ہوا سے بچنے کے لیے فصلیں لگائیں۔",
        "استاد نے مشکل الفاظ کے معنی آسانی سے سمجھا دیے۔",
        "خوفزدہ خرگوش جھاڑیوں میں چھپ گیا۔",
        "نغمہ خوان پرندوں نے صبح کا استقبال کیا۔",
    ],
}


def calculate_wcpm(raw_wpm: float, accuracy_ratio: float, pause_count: int = 0, persona_type: str = "child") -> float:
    """Words Correct Per Minute (WCPM) formula with dyslexia accommodation."""
    if persona_type == "dyslexia":
        return round(raw_wpm * accuracy_ratio, 1)
    pause_penalty = min(20.0, pause_count * 1.5)
    return max(0.0, round((raw_wpm * accuracy_ratio) - pause_penalty, 1))


@router.get("/sentences")
async def generate_sentences(difficulty: str = "medium", count: int = 5, language: str = "en"):
    """Fresh warm-up sentences for the classic dashboard, generated by the
    diagnosis model in the requested difficulty; static banks offline.
    Called on dashboard load and on every shuffle, so reads never start from
    the same five stock sentences."""
    difficulty = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    count = max(1, min(count, 8))
    language = require_reading_language(language)
    try:
        from agents.orchestrator import call_agent
        data = await asyncio.wait_for(
            call_agent(SENTENCE_PROMPT, {
                "difficulty": difficulty, "grade": 3, "count": count,
                "output_language": "Urdu (اردو)" if language == "ur" else "Spanish (Español)" if language == "es" else "English",
            }),
            timeout=12)
        raw_sentences = data.get("sentences")
        if not isinstance(raw_sentences, list):
            raise ValueError("Sentence generation must return a list")
        sentences = [s.strip() for s in raw_sentences
                     if isinstance(s, str) and 5 <= len(s.strip()) <= 500][:count]
        if len(sentences) >= 3:
            return {"sentences": sentences, "difficulty": difficulty, "source": "meta"}
    except Exception as e:
        print(f"[SENTENCES] generation failed, using bank: {e}")
    bank = (SENTENCE_BANKS_UR if language == "ur" else SENTENCE_BANKS_ES if language == "es" else SENTENCE_BANKS)[difficulty][:]
    random.shuffle(bank)
    return {"sentences": bank[:count], "difficulty": difficulty,
            "language": language, "source": "fallback"}


def _process_audio(audio_path: str, target_sentence: str, grade: int, language: str = "en") -> dict:
    """
    Transcription + acoustics for the classic engine.

    STT uses the same source logic as the v2 layer (services/stt.py):
    Groq Whisper online (~1s, word timestamps) with automatic fallback to the
    local faster-whisper/openai-whisper model when offline — so a reading
    session still works with no internet. Pitch/pause acoustics stay local
    (librosa) because STT APIs don't return pitch.
    """
    from services.stt import get_transcript
    from services import acoustic
    started = time.perf_counter()
    stt = get_transcript(audio_path, language)
    stt_ms = (time.perf_counter() - started) * 1000
    acoustic_started = time.perf_counter()
    acoustics = acoustic.extract_word_acoustics(audio_path, stt.words)
    acoustic_ms = (time.perf_counter() - acoustic_started) * 1000
    scoring_started = time.perf_counter()
    signal = acoustic.build_signal(target_sentence, stt, acoustics, language, stt_ms, acoustic_ms, 0)
    signal["latency_ms"]["scoring"] = round((time.perf_counter() - scoring_started) * 1000)
    signal["latency_ms"]["total_phase1"] = round((time.perf_counter() - started) * 1000)
    return {**signal, "words_spoken": stt.words, "word_results": signal["words"],
            "pause_count": len(signal["hesitations"]) if signal["speech_evidence"]["pause_assessment"]=="available" else None, "pauses": signal["hesitations"],
            "pause_durations": [p["pause_ms"] for p in signal["hesitations"]],
            "session_duration_seconds": acoustics["total_duration"], "pitch_series": [],
            "repetition_count": 0, "hesitation_count": len(signal["hesitations"]),
            "grade": grade, "target_sentence": target_sentence, "language": language}


@router.post("/run")
async def execute_pipeline(request: PipelineRunRequest):
    # ── 1. Fetch student + session history ────────────────────────────────────
    student_grade = 3
    session_history = []

    with get_db_connection() as conn:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?", (request.student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        student_grade = student["grade"]

        history_rows = conn.execute(
            "SELECT * FROM sessions WHERE student_id = ? AND language = ? AND is_mock=0 ORDER BY timestamp DESC, rowid DESC LIMIT 10",
            (request.student_id, request.language),
        ).fetchall()
        session_history = [dict(r) for r in history_rows]

    # ── 2. Build signal_data ───────────────────────────────────────────────────
    signal_data = {}

    if request.mocked_signal_data:
        if os.getenv("ENABLE_MOCK_ANALYSIS") != "1" or os.getenv("ENV") == "production":
            raise HTTPException(404, "Simulated analysis is disabled")
        # Simulations are returned without persisting learner progress.
        signal_data = dict(request.mocked_signal_data)
        signal_data["grade"] = student_grade
        signal_data["target_sentence"] = request.target_sentence

    elif request.audio_base64:
        # Real mode: decode audio → Whisper + Librosa → structured features
        try:
            audio_bytes = base64.b64decode(request.audio_base64, validate=True)
        except (ValueError, __import__("binascii").Error):
            raise HTTPException(422, "Invalid audio encoding")
        if not 1000 <= len(audio_bytes) <= 10 * 1024 * 1024:
            raise HTTPException(422, "Recording must contain audio and be no larger than 10 MB")

        # Detect audio format from the first bytes (magic bytes)
        # WebM: starts with 0x1A 0x45 0xDF 0xA3
        # OGG:  starts with b'OggS'
        # MP4/M4A: bytes 4-8 == b'ftyp'
        ext = ".webm"  # default — most browsers use webm
        if audio_bytes[:4] == b'OggS':
            ext = ".ogg"
        elif len(audio_bytes) > 8 and audio_bytes[4:8] == b'ftyp':
            ext = ".mp4"
        elif audio_bytes[:4] == b'RIFF':
            ext = ".wav"
        elif audio_bytes[:3] == b'ID3' or (len(audio_bytes) > 2 and audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0):
            ext = ".mp3"

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            print(f"[DSP] Audio format detected: {ext}, size: {len(audio_bytes)} bytes")
            signal_data = await run_audio(_process_audio, tmp_path, request.target_sentence, student_grade, request.language)

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, "Audio processing failed. Check the recording and speech engine setup.")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either audio_base64 or mocked_signal_data.",
        )

    # ── 3.5 Per-word correctness from real alignment (same engine as Story
    #        Mode) — the transcript must be colored by measurement, not by the
    #        agents' word list ──────────────────────────────────────────────────
    from services.acoustic import align_words, score_word, tokenize
    word_results = signal_data.get("word_results")
    if word_results is None:
        entries = align_words(request.target_sentence, signal_data.get("words_spoken") or [])
        word_results = [score_word(e, {"word_features": {}}) for e in entries if e["target"]]
        for entry in entries:
            word_results.extend({"word": word, "correct": False, "score": 15,
                                 "phoneme_mismatch": "extra word", "spoken": word, "extra": True}
                                for word in entry.get("extra_words", []))
    extras = sum(bool(word.get("extra")) for word in word_results)
    correct_words = sum(bool(word["correct"]) for word in word_results)
    total_words = max(1, len(tokenize(request.target_sentence)) + extras)
    accuracy_percentage = round(100 * correct_words / total_words)
    accuracy_ratio = correct_words / total_words

    # Resolve reader persona (accommodates dyslexia by waiving speed and pause penalties)
    persona_type = "child"
    if request.student_id:
        try:
            with get_db_connection() as conn:
                urow = conn.execute(
                    "SELECT up.reader_mode FROM user_profiles up JOIN users u ON u.id=up.user_id WHERE u.student_id=?",
                    (request.student_id,)
                ).fetchone()
                if urow and urow["reader_mode"]:
                    persona_type = urow["reader_mode"]
        except Exception:
            pass

    raw_wpm = float(signal_data.get("wpm", 0.0))
    raw_pauses = signal_data.get("pauses") or []
    pause_count = len(raw_pauses)

    # Words Correct Per Minute (WCPM) calculation
    # Waive raw speed and pause deductions for dyslexic readers so slow accurate reading is rewarded
    if persona_type == "dyslexia":
        wcpm = round(raw_wpm * accuracy_ratio, 1)
        overall_score = accuracy_percentage
    else:
        pause_penalty = min(20.0, pause_count * 1.5)
        wcpm = max(0.0, round((raw_wpm * accuracy_ratio) - pause_penalty, 1))
        overall_score = max(0, min(100, round((accuracy_percentage * 0.7) + (min(100, wcpm) * 0.3))))

    # Coaching and UI use exactly the same observations and current score.
    signal_data.update(
        word_results=word_results,
        accuracy=accuracy_percentage,
        wpm=raw_wpm,
        wcpm=wcpm,
        overall_score=overall_score,
        persona_type=persona_type,
        target_sentence=request.target_sentence,
        language=request.language,
    )
    results = await run_pipeline(signal_data, session_history)

    # ── 5. Persist to database ─────────────────────────────────────────────────
    session_id = str(uuid.uuid4())
    transcript = signal_data.get("transcript", "")

    try:
        if request.mocked_signal_data:
            raise _SimulationOnly()
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                    (id, student_id, target_sentence, transcript, wpm, accuracy, overall_score, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    request.student_id,
                    request.target_sentence,
                    transcript,
                    signal_data.get("wpm", 0.0),
                    round(accuracy_percentage / 100, 2),
                    overall_score,
                    getattr(request, "language", "en") or "en",
                ),
            )
            conn.execute(
                """
                INSERT INTO diagnoses
                    (session_id, phonetic_result, difficulty_result,
                     engagement_result, practice_result, progress_result)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    json.dumps(results["phonetic"]),
                    json.dumps(results["difficulty"]),
                    json.dumps(results["engagement"]),
                    json.dumps(results["practice"]),
                    json.dumps(results["progress"]),
                ),
            )
            save_speech_evidence(conn,'classic',session_id,signal_data.get('speech_evidence'))
            conn.commit()
            conn.execute("UPDATE sessions SET words_json=? WHERE id=?", (json.dumps(word_results, ensure_ascii=False), session_id))
            conn.commit()
        print(f"[DB] Session {session_id} saved.")
    except _SimulationOnly:
        session_id = "simulation"
    except Exception:
        raise HTTPException(503, "The attempt could not be saved. Please retry.")

    # ── 6. Return full response to frontend ────────────────────────────────────
    return {
        "session_id":   session_id,
        "transcript":   transcript,
        "wpm":          signal_data.get("wpm", 0),
        "wcpm":         signal_data.get("wcpm", 0.0),
        "overall_score": overall_score,
        "accuracy":     accuracy_percentage,
        "pauses":       len(signal_data.get("pauses") or []) if signal_data.get('speech_evidence',{}).get('pause_assessment')=='available' else None,
        "speech_evidence": signal_data.get('speech_evidence'),
        "latency_ms":   signal_data.get("latency_ms", {}),
        "stt_source":   signal_data.get("stt_source", "local_fallback"),
        "language":     getattr(request, "language", "en") or "en",
        "words_spoken": signal_data.get("words_spoken", []),
        "words":        word_results,
        "diagnosis":    results,
    }
