"""
Role-based authentication (teacher / student).

Flow: students self-register -> account sits in `pending` -> a teacher approves
from the Settings page -> the account links to a roster entry so Story Mode
sessions bind to the right student. Tokens are opaque random strings stored in
SQLite (Authorization: Bearer <token>).
"""
import uuid
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from core.security import hash_password, verify_password, new_token
from database.schema import get_db_connection

log = logging.getLogger("speakflow.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class StudentApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: str | None = Field(default=None, min_length=1, max_length=100)


def _text(body, key, maximum=256):
    value = body.get(key, "")
    if not isinstance(value, str) or len(value) > maximum:
        raise HTTPException(422, f"Invalid {key}")
    return value


def _user_dict(row) -> dict:
    d = dict(row)
    d.pop("password_hash", None)
    if d.get("role") == "teacher":
        with get_db_connection() as conn:
            classroom = conn.execute("SELECT join_code FROM classrooms WHERE id=?", (d.get("classroom_id"),)).fetchone()
        d["classroom_code"] = classroom["join_code"] if classroom else None
    return d


def get_current_user(request: Request) -> dict | None:
    """Resolve the Bearer token to a user row, or None."""
    if request is None:
        return None
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):].strip()
    if not token:
        return None
    with get_db_connection() as conn:
        row = conn.execute(
            """SELECT u.* FROM auth_tokens t
               JOIN users u ON u.id = t.user_id
               WHERE t.token = ? AND t.expires_at > datetime('now') AND u.status='approved'
               AND (u.role='teacher' OR EXISTS (
                   SELECT 1 FROM students s WHERE s.id=u.student_id AND s.archived=0 AND s.classroom_id=u.classroom_id))""",
            (token,)).fetchone()
    return _user_dict(row) if row else None


def require_teacher(user: dict | None) -> JSONResponse | None:
    """Return a 403 envelope response when the user is not an approved teacher."""
    if not user or user["role"] != "teacher" or user["status"] != "approved":
        return JSONResponse(status_code=403, content={
            "error": {"code": "VALIDATION_ERROR",
                      "message": "Teacher access required", "retryable": False}})
    return None


def _json_error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={
        "error": {"code": "VALIDATION_ERROR", "message": message, "retryable": False}})


@router.post("/register")
async def register(body: dict):
    name = _text(body, "name", 120).strip()
    username = _text(body, "username", 64).strip().lower()
    password = _text(body, "password")
    classroom_code = _text(body, "classroom_code", 128).strip()
    if not name or not username or len(password) < 10:
        return _json_error("Name, username and a password of at least 10 characters are required.")
    if not all(c.isalnum() or c in "._-" for c in username):
        return _json_error("Usernames can only contain letters, numbers, dots, dashes and underscores.")

    with get_db_connection() as conn:
        classroom = conn.execute("SELECT id FROM classrooms WHERE join_code=?", (classroom_code,)).fetchone()
        if not classroom:
            return _json_error("A valid classroom code from your teacher is required.", 422)
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return _json_error("That username is already taken.", 409)
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        conn.execute(
            """INSERT INTO users (id, username, name, password_hash, role, status, classroom_id)
               VALUES (?, ?, ?, ?, 'student', 'pending', ?)""",
            (user_id, username, name, hash_password(password), classroom["id"]))
        conn.commit()

    return {
        "ok": True,
        "message": "Account created! Your teacher will approve it shortly — then you can log in.",
        "status": "pending",
    }


@router.post("/login")
async def login(body: dict):
    username = _text(body, "username", 64).strip().lower()
    password = _text(body, "password")
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return _json_error("Wrong username or password.", 401)
    user = _user_dict(row)
    if user["status"] == "pending":
        return JSONResponse(status_code=403, content={
            "error": {"code": "VALIDATION_ERROR", "retryable": False,
                      "message": "Your account is waiting for teacher approval. "
                                 "Please check back soon!"}})
    if user["status"] not in {"approved", "pending"}:
        return JSONResponse(status_code=403, content={
            "error": {"code": "VALIDATION_ERROR", "retryable": False,
                      "message": "This account was not approved. Please talk to your teacher."}})

    token = new_token()
    with get_db_connection() as conn:
        conn.execute("INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, datetime('now', '+24 hours'))",
                     (token, user["id"]))
        conn.commit()
    return {"token": token, "user": user}


@router.post("/logout")
async def logout(request: Request):
    if request is None:
        return None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?",
                         (auth[len("Bearer "):].strip(),))
            conn.commit()
    return {"ok": True}


@router.get("/me")
async def me(request: Request):
    user = get_current_user(request)
    if not user:
        return _json_error("Not logged in.", 401)
    return {"user": user}


@router.post("/change-password")
async def change_password(body: dict, request: Request):
    user = get_current_user(request)
    if not user:
        return _json_error("Not logged in.", 401)
    current = _text(body, "current_password")
    new = _text(body, "new_password")
    if len(new) < 10:
        return _json_error("New password needs at least 10 characters.")
    with get_db_connection() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?",
                           (user["id"],)).fetchone()
        if not row or not verify_password(current, row["password_hash"]):
            return _json_error("Your current password is not correct.", 401)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                     (hash_password(new), user["id"]))
        conn.execute("DELETE FROM auth_tokens WHERE user_id=?", (user["id"],))
        conn.commit()
    return {"ok": True, "message": "Password updated. Please log in again."}


# ── Teacher: account management ──────────────────────────────────────────────
@router.get("/users")
async def list_users(request: Request):
    forbidden = require_teacher(get_current_user(request))
    if forbidden:
        return forbidden
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE classroom_id=? ORDER BY status = 'pending' DESC, created_at DESC",
            (get_current_user(request)["classroom_id"],)).fetchall()
    return [_user_dict(r) for r in rows]


@router.post("/users/{user_id}/approve")
async def approve_user(user_id: str, request: Request, body: StudentApproval | None = None):
    teacher = get_current_user(request)
    forbidden = require_teacher(teacher)
    if forbidden:
        return forbidden
    with get_db_connection() as conn:
        # Serialize selection/check/update so two approvals cannot claim one profile.
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM users WHERE id = ? AND classroom_id=?", (user_id, teacher["classroom_id"])).fetchone()
        if not row:
            return _json_error("User not found.", 404)
        if row["role"] != "student":
            return _json_error("Teacher accounts must be managed by the administrator.", 403)
        requested_id = body.student_id if body else None
        if row["student_id"] and requested_id and row["student_id"] != requested_id:
            return _json_error("This account already has a reader profile. Its history cannot be reassigned here.", 409)
        if row["status"] == "approved":
            return {"ok": True, "student_id": row["student_id"], "created_profile": False}
        # Approve + link (or create) the roster entry so story sessions work
        student_id = row["student_id"] or requested_id
        if student_id:
            profile = conn.execute("SELECT id,archived FROM students WHERE id=? AND classroom_id=?",
                                   (student_id, teacher["classroom_id"])).fetchone()
            if not profile:
                return _json_error("Reader profile not found in your classroom.", 404)
            if profile["archived"]:
                return _json_error("Restore the archived reader profile before approving this account.", 422)
            linked = conn.execute("SELECT id FROM users WHERE student_id=? AND id<>?", (student_id, user_id)).fetchone()
            if linked:
                return _json_error("That reader profile already has an account. Choose another profile or create a new one.", 409)
        created_profile = not student_id
        if not student_id:
            student_id = f"stu-{uuid.uuid4().hex[:8]}"
            conn.execute(
                """INSERT INTO students (id, name, grade, level, classroom_id)
                   VALUES (?, ?, 3, 'Level 1', ?)""",
                (student_id, row["name"], row["classroom_id"]))
        conn.execute(
            "UPDATE users SET status = 'approved', student_id = ? WHERE id = ?",
            (student_id, user_id))
        conn.commit()
    return {"ok": True, "student_id": student_id, "created_profile": created_profile}


@router.post("/users/{user_id}/reject")
async def reject_user(user_id: str, request: Request):
    forbidden = require_teacher(get_current_user(request))
    if forbidden:
        return forbidden
    with get_db_connection() as conn:
        target = conn.execute("SELECT classroom_id, role FROM users WHERE id=?", (user_id,)).fetchone()
        if not target or target["classroom_id"] != get_current_user(request)["classroom_id"]:
            return _json_error("User not found.", 404)
        if target["role"] == "teacher":
            return _json_error("Teacher accounts must be managed by the administrator.", 403)
        conn.execute("DELETE FROM auth_tokens WHERE user_id=?", (user_id,))
        conn.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
        conn.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    me_user = get_current_user(request)
    forbidden = require_teacher(me_user)
    if forbidden:
        return forbidden
    if me_user and me_user["id"] == user_id:
        return _json_error("You cannot delete your own account.", 422)
    with get_db_connection() as conn:
        target = conn.execute("SELECT classroom_id, role FROM users WHERE id=?", (user_id,)).fetchone()
        if not target or target["classroom_id"] != get_current_user(request)["classroom_id"]:
            return _json_error("User not found.", 404)
        if target["role"] == "teacher":
            return _json_error("Teacher accounts must be managed by the administrator.", 403)
        conn.execute("DELETE FROM auth_tokens WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return {"ok": True}
