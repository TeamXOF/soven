"""Create/reset an administrator without shipping a shared default password.

Run from backend: python scripts/bootstrap_teacher.py --username teacher
Password is prompted securely. --classroom selects an independent classroom.
"""
import argparse
import getpass
from pathlib import Path
import secrets
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.schema import init_db, get_db_connection
from core.security import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="teacher")
    parser.add_argument("--check", action="store_true", help="Exit successfully when an approved administrator exists")
    parser.add_argument("--classroom", default="default")
    args = parser.parse_args()
    if args.check:
        init_db()
        with get_db_connection() as conn:
            ready = conn.execute("SELECT 1 FROM users WHERE role='teacher' AND status='approved' AND is_admin=1 LIMIT 1").fetchone()
        raise SystemExit(0 if ready else 1)
    password = getpass.getpass("New teacher password (at least 10 characters): ")
    if len(password) < 10 or password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords must match and contain at least 10 characters")
    init_db()
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO classrooms(id,join_code) VALUES (?,?)", (args.classroom, secrets.token_urlsafe(12)))
        old = conn.execute("SELECT id FROM users WHERE username=?", (args.username.lower(),)).fetchone()
        if old:
            conn.execute("UPDATE users SET password_hash=?,role='teacher',status='approved',classroom_id=?,is_admin=1 WHERE id=?", (hash_password(password), args.classroom, old["id"]))
            conn.execute("DELETE FROM auth_tokens WHERE user_id=?", (old["id"],))
        else:
            conn.execute("INSERT INTO users(id,username,name,password_hash,role,status,classroom_id,is_admin) VALUES (?,?,?,?,'teacher','approved',?,1)", (uuid.uuid4().hex, args.username.lower(), args.username, hash_password(password), args.classroom))
        teacher = conn.execute('SELECT id FROM users WHERE username=?', (args.username.lower(),)).fetchone()
        from core.reader_profiles import create_profile
        create_profile(conn, teacher['id'], 'teacher', completed=True)
        conn.execute("UPDATE user_profiles SET reader_mode='teacher',profile_completed=1 WHERE user_id=?", (teacher['id'],))
        code = conn.execute("SELECT join_code FROM classrooms WHERE id=?", (args.classroom,)).fetchone()[0]
        conn.commit()
    print(f"Teacher configured. Classroom join code: {code}")


if __name__ == "__main__":
    main()
