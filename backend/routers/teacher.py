"""
Teacher-facing management endpoints: live roster stats, parent auto-update
toggle + real generated messages, downloadable reports, a practice library
derived from actual errors, and runtime API-key management (persisted to .env).

All routes require an approved teacher unless noted.
"""
import os
import json
import uuid
import logging
import tempfile
import threading
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from core.config import settings
from database.schema import get_db_connection
from routers.auth import get_current_user, require_teacher

log = logging.getLogger("speakflow.teacher")

router = APIRouter(prefix="/api/v1", tags=["teacher"])

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
with open(os.path.join(_DATA, "stories.json"), encoding="utf-8") as _f:
    STORIES = {s["id"]: s for s in json.load(_f)["stories"]}

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(_BACKEND_DIR, ".env")
_env_lock = threading.Lock()


def _teacher(request: Request) -> JSONResponse | None:
    return require_teacher(get_current_user(request))


def _per_student_stats(conn) -> dict:
    """One aggregate row per student from real checkpoint + session data."""
    rows = conn.execute(
        """
        SELECT ss.student_id,
               COUNT(cr.id) AS attempted,
               SUM(cr.passed) AS passed,
               SUM(cr.stars) AS stars,
               AVG(cr.accuracy) AS avg_accuracy,
               MAX(cr.created_at) AS last_checkpoint
        FROM checkpoint_results cr
        JOIN story_sessions ss ON ss.id = cr.session_id
        GROUP BY ss.student_id
        """).fetchall()
    stats = {}
    for r in rows:
        d = dict(r)
        stats[d["student_id"]] = {
            "attempted": int(d["attempted"] or 0),
            "passed": int(d["passed"] or 0),
            "stars": int(d["stars"] or 0),
            "avg_accuracy": int(round(d["avg_accuracy"])) if d["avg_accuracy"] is not None else None,
            "last_active": d["last_checkpoint"],
        }
    return stats


# ── Roster with real stats ───────────────────────────────────────────────────
@router.get("/teacher/roster")
def teacher_roster(request: Request = None):
    from services import analytics
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": {"message": "Please log in"}})
    return analytics.roster(user)


# ── Parent auto-update preference ────────────────────────────────────────────
@router.post("/teacher/students/{student_id}/parent-toggle")
def toggle_parent_updates(student_id: str, body: dict, request: Request = None):
    forbidden = _teacher(request)
    if forbidden:
        return forbidden
    enabled = 1 if body.get("enabled") else 0
    with get_db_connection() as conn:
        row = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "error": {"code": "VALIDATION_ERROR", "message": "Student not found",
                          "retryable": False}})
        conn.execute(
            "UPDATE students SET parent_update_enabled = ? WHERE id = ?",
            (enabled, student_id))
        conn.commit()
    return {"ok": True, "enabled": bool(enabled)}


def _build_parent_message(conn, student_id: str) -> dict:
    """Real weekly parent update assembled from actual session data (Urdu)."""
    with get_db_connection() as conn:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not student:
            return {"enabled": False, "message": None}
        enabled = bool(student["parent_update_enabled"])
        last = conn.execute(
            """
            SELECT cr.accuracy, cr.stars, cr.words_json, cr.created_at, ss.story_id
            FROM checkpoint_results cr
            JOIN story_sessions ss ON ss.id = cr.session_id
            WHERE ss.student_id = ?
            ORDER BY cr.created_at DESC LIMIT 1
            """, (student_id,)).fetchone()
        totals = conn.execute(
            """
            SELECT SUM(cr.stars) AS stars, SUM(cr.passed) AS passed, COUNT(cr.id) AS attempted
            FROM checkpoint_results cr
            JOIN story_sessions ss ON ss.id = cr.session_id
            WHERE ss.student_id = ?
            """, (student_id,)).fetchone()

    if not enabled:
        return {"enabled": False, "message": None, "student_name": student["name"]}

    if not last:
        message = (f"السلام علیکم! {student['name']} نے ابھی تک کوئی چیک پوائنٹ مکمل نہیں کیا۔ "
                   f"جس دن پڑھائی شروع ہوگی ہم آپ کو اطلاع دیں گے!")
        return {"enabled": True, "message": message, "student_name": student["name"]}

    story = STORIES.get(last["story_id"], {})
    title = story.get("title_ur") or story.get("title", "کہانی")
    acc = int(round(last["accuracy"] or 0))
    total_stars = int(totals["stars"] or 0)

    # Top struggling word from the last checkpoint's real word data
    tricky = None
    try:
        for w in json.loads(last["words_json"] or "[]"):
            if not w["correct"]:
                tricky = w["word"]
                break
    except json.JSONDecodeError:
        pass

    parts = [
        f"السلام علیکم! {student['name']} نے '{title}' کہانی کا چیک پوائنٹ پڑھا۔",
        f"درستگی {acc}% رہی اور کل {total_stars} ستارے جمع ہوئے۔",
    ]
    if tricky:
        parts.append(f"مشق کا لفظ: '{tricky}' — برائے مہربانی گھر پر ایک بار دہرائیں۔")
    if acc >= 85:
        parts.append("بہت خوب! جاری رکھیں!")
    else:
        parts.append("محنت جاری رکھیں — ہم روز بہتر ہو رہے ہیں!")
    return {
        "enabled": True,
        "message": " ".join(parts),
        "student_name": student["name"],
        "based_on": {"date": last["created_at"], "accuracy": acc},
    }


@router.get("/students/{student_id}/parent-message")
def parent_message(student_id: str, request: Request = None):
    from services import analytics
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": {"message": "Please log in"}})
    return analytics.parent_message(user, student_id)


# ── Reports (real data, downloadable) ────────────────────────────────────────
@router.get("/reports")
def reports(request: Request = None):
    from services import analytics
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": {"message": "Please log in"}})
    return analytics.reports(user)


# ── Practice library derived from REAL errors ────────────────────────────────
@router.get("/practice/library")
def practice_library(request: Request = None):
    from services import analytics
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": {"message": "Please log in"}})
    return analytics.practice(user)


# ── Runtime API-key management (teacher only, persisted to .env) ─────────────
def _write_env_key(key: str, value: str):
    """Replace or append KEY=... in backend/.env and live-update the process."""
    if "\n" in value or "\r" in value:
        raise HTTPException(422, "Configuration values must fit on one line")
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.read().splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            lines[i] = f"{key}={value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{key}={value}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=os.path.dirname(ENV_PATH), delete=False) as f:
            temporary = f.name
            os.chmod(temporary, 0o600)
            f.write("\n".join(lines).rstrip() + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, ENV_PATH)
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)
    os.environ[key] = value


def _set_env_key(key: str, value: str):
    with _env_lock:
        _write_env_key(key, value)


@router.get("/config/keys")
def get_keys(request: Request = None):
    forbidden = _teacher(request)
    if forbidden:
        return forbidden
    return {
        "groq_configured": bool(settings.GROQ_API_KEY),
        "google_configured": bool(settings.active_gemini_key),
        "google_key_count": len([k for k in settings.active_gemini_key.split(",") if k.strip()]),
        "env": settings.ENV,
        "stt_mode": settings.stt_mode,
        "agent_model": settings.agent_model,
    }


STT_MODES = ("auto", "groq", "local")
AGENT_MODELS = ("auto", "gemini-3.5-flash-lite", "gemma-4-31b-it")


@router.post("/config/keys")
def set_keys(body: dict, request: Request = None):
    forbidden = _teacher(request)
    if forbidden:
        return forbidden
    updated = []

    groq_key = (body.get("groq_api_key") or "").strip()
    if groq_key:
        _set_env_key("GROQ_API_KEY", groq_key)
        settings.GROQ_API_KEY = groq_key
        updated.append("GROQ_API_KEY")

    google_keys = (body.get("google_api_keys") or "").strip()
    if google_keys:
        _set_env_key("GOOGLE_API_KEYS", google_keys)
        os.environ["GOOGLE_API_KEYS"] = google_keys
        # Reconfigure the live Gemini client with the new key(s)
        from services import reasoning
        reasoning._configure_key()
        updated.append("GOOGLE_API_KEYS")

    # Engine picks (Settings → live-apply + persist to .env)
    stt_mode = (body.get("stt_mode") or "").strip().lower()
    if stt_mode:
        if stt_mode not in STT_MODES:
            return JSONResponse(status_code=422, content={
                "error": {"code": "VALIDATION_ERROR",
                          "message": f"stt_mode must be one of {STT_MODES}",
                          "retryable": False}})
        _set_env_key("STT_MODE", stt_mode)
        updated.append("STT_MODE")

    agent_model = (body.get("agent_model") or "").strip()
    if agent_model:
        if agent_model not in AGENT_MODELS:
            return JSONResponse(status_code=422, content={
                "error": {"code": "VALIDATION_ERROR",
                          "message": f"agent_model must be one of {AGENT_MODELS}",
                          "retryable": False}})
        _set_env_key("GEN1_AGENT_MODEL", agent_model)
        updated.append("GEN1_AGENT_MODEL")

    return {
        "ok": True,
        "updated": updated,
        "groq_configured": bool(settings.GROQ_API_KEY),
        "google_configured": bool(settings.active_gemini_key),
        "stt_mode": settings.stt_mode,
        "agent_model": settings.agent_model,
    }
