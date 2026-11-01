from fastapi import APIRouter, HTTPException, Request
from routers.auth import get_current_user
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from database.schema import get_db_connection

router = APIRouter(prefix="/api/students", tags=["students"])

class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    grade: int = Field(ge=1, le=12)
    level: str = Field(default="Level 1", min_length=1, max_length=80)

class StudentResponse(BaseModel):
    id: str
    name: str
    grade: int
    level: str
    created_at: str

@router.get("/", response_model=List[StudentResponse])
def get_students(request: Request):
    user = get_current_user(request)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE archived=0 AND classroom_id=? AND (?='teacher' OR id=?) ORDER BY name ASC",
                       (user["classroom_id"], user["role"], user.get("student_id")))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, request: Request):
    student_id = f"stu-{str(uuid.uuid4())[:8]}"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (id, name, grade, level, classroom_id) VALUES (?, ?, ?, ?, ?)",
            (student_id, student.name, student.grade, student.level, get_current_user(request)["classroom_id"])
        )
        conn.commit()
        
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row)

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student not found")
        return dict(row)

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, student: StudentCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET name = ?, grade = ?, level = ? WHERE id = ?",
            (student.name, student.grade, student.level, student_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        conn.commit()
        
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        return dict(cursor.fetchone())

@router.delete("/{student_id}")
def delete_student(student_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Archive the learner; keep historical attempts recoverable.
        cursor.execute("UPDATE students SET archived=1 WHERE id = ?", (student_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        cursor.execute("DELETE FROM auth_tokens WHERE user_id IN (SELECT id FROM users WHERE student_id=?)", (student_id,))
        cursor.execute("UPDATE users SET status='rejected' WHERE student_id=?", (student_id,))
        conn.commit()
        return {"status": "success", "message": "Student archived"}
