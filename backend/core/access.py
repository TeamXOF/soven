"""Shared record ownership checks for HTTP and WebSocket entry points."""
from fastapi import HTTPException
from database.schema import get_db_connection


def authorize_student(user: dict, student_id: str):
    with get_db_connection() as conn:
        row = conn.execute("SELECT classroom_id FROM students WHERE id = ? AND archived=0", (student_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Student not found")
    if row["classroom_id"] != user["classroom_id"]:
        raise HTTPException(403, "Student access denied")
    if user["role"] != "teacher" and user.get("student_id") != student_id:
        raise HTTPException(403, "Student access denied")


def authorize_record(user: dict, table: str, record_id: str):
    if table not in {"sessions", "story_sessions", "story_attempts"}:
        raise ValueError("Unsupported resource")
    with get_db_connection() as conn:
        row = conn.execute(f"SELECT student_id FROM {table} WHERE id = ?", (record_id,)).fetchone()
        if not row and table == "story_sessions":
            row = conn.execute("SELECT student_id FROM story_attempts WHERE id=? AND is_mock=0", (record_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Reading record not found")
    authorize_student(user, row["student_id"])


def classroom_id(request) -> str:
    from routers.auth import get_current_user
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Please log in")
    return user["classroom_id"]
