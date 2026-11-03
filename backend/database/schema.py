import sqlite3
import os
from contextlib import contextmanager, closing
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

# Always resolve to absolute path from the backend directory
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_db_env = os.getenv("DATABASE_URL", "speakflow.db")
# If the env path is relative, make it absolute relative to backend dir
DB_PATH = _db_env if os.path.isabs(_db_env) else os.path.join(_BACKEND_DIR, os.path.basename(_db_env))

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    # SQLite's backup API gives a consistent copy even when WAL is in use.
    # Never migrate an existing, unversioned classroom without a recovery copy.
    if os.path.isfile(DB_PATH):
        with closing(sqlite3.connect(DB_PATH)) as source:
            versioned = source.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()
            needs_profile_backup = bool(versioned) and not source.execute(
                'SELECT 1 FROM schema_migrations WHERE version=3').fetchone()
            if not versioned or needs_profile_backup:
                backup_dir = Path(DB_PATH).parent / ".db_backup"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / (Path(DB_PATH).stem + ("-before-profiles.db" if needs_profile_backup else "-before-hardening.db"))
                if not backup_path.exists():
                    with closing(sqlite3.connect(backup_path)) as destination:
                        source.backup(destination)
    with get_db_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            grade INTEGER NOT NULL,
            level TEXT DEFAULT 'Level 1',
            created_at TEXT DEFAULT (datetime('now'))
        )
        ''')
        
        # Sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            student_id TEXT REFERENCES students(id),
            target_sentence TEXT,
            transcript TEXT,
            audio_path TEXT,
            wpm REAL,
            accuracy REAL,
            overall_score INTEGER,
            timestamp TEXT DEFAULT (datetime('now'))
        )
        ''')
        
        # Signal data table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_data (
            session_id TEXT PRIMARY KEY REFERENCES sessions(id),
            pauses TEXT,
            pitch_series TEXT,
            pitch_variance REAL,
            repetition_count INTEGER DEFAULT 0,
            hesitation_count INTEGER DEFAULT 0
        )
        ''')
        
        # Diagnoses table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnoses (
            session_id TEXT PRIMARY KEY REFERENCES sessions(id),
            phonetic_result TEXT,
            difficulty_result TEXT,
            engagement_result TEXT,
            practice_result TEXT,
            progress_result TEXT
        )
        ''')
        
        # Seed demo student if not exists
        cursor.execute('''
        INSERT OR IGNORE INTO students (id, name, grade, level, created_at)
        VALUES ('student-1', 'Aarav Sharma', 3, 'Level 2', datetime('now'))
        ''')

        # ── v2 checkpoint-based sessions (roadmap API contract) ────────────────
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_sessions (
            id TEXT PRIMARY KEY,
            student_id TEXT REFERENCES students(id),
            story_id TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            synced INTEGER DEFAULT 1,
            mode TEXT DEFAULT 'online'
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkpoint_results (
            id TEXT PRIMARY KEY,
            session_id TEXT REFERENCES story_sessions(id),
            checkpoint_id TEXT NOT NULL,
            target_text TEXT,
            transcript TEXT,
            wpm REAL,
            accuracy REAL,
            passed INTEGER DEFAULT 0,
            stars INTEGER DEFAULT 0,
            words_json TEXT,
            hesitations_json TEXT,
            feedback_text TEXT,
            engagement_state TEXT,
            comprehension_question TEXT,
            practice_recommendation TEXT,
            teacher_note TEXT,
            stt_source TEXT,
            feedback_source TEXT,
            latency_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(session_id, checkpoint_id)
        )
        ''')

        # ── Auth & roles (teacher / student accounts) ──────────────────────────
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            status TEXT NOT NULL DEFAULT 'pending',
            student_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        )
        ''')

        # Per-word pronunciation tips (tap-a-word feature). Cached: each word is
        # generated once, then served from here forever.
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_tips (
            word TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            tip TEXT NOT NULL,
            syllables_json TEXT,
            source TEXT DEFAULT 'template',
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (word, language)
        )
        ''')

        # Parent auto-update preference (may be missing on pre-existing DBs)
        try:
            cursor.execute(
                "ALTER TABLE students ADD COLUMN parent_update_enabled INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # column already exists

        # ── Dynamic Story Mode (endless dual-track levels) ──────────────────
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_levels (
            track TEXT NOT NULL,
            level INTEGER NOT NULL,
            sentence TEXT NOT NULL,
            theme TEXT,
            difficulty TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (track, level)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_progress (
            student_id TEXT NOT NULL,
            track TEXT NOT NULL,
            level INTEGER NOT NULL,
            best_accuracy INTEGER DEFAULT 0,
            stars INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (student_id, track, level)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_attempts (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            track TEXT,
            level INTEGER,
            accuracy INTEGER,
            stars INTEGER,
            passed INTEGER,
            result_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_phase2 (
            attempt_id TEXT PRIMARY KEY,
            payload_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        ''')

        # Reading language of classic-engine sessions ("en" | "ur") — added
        # when Urdu support landed so progress tracking can tell them apart
        try:
            cursor.execute(
                "ALTER TABLE sessions ADD COLUMN language TEXT DEFAULT 'en'")
        except sqlite3.OperationalError:
            pass  # column already exists

        # Additive, idempotent migrations preserve existing learner records.
        migrations = {
            "users": [("classroom_id", "TEXT NOT NULL DEFAULT 'default'"), ("is_admin", "INTEGER NOT NULL DEFAULT 0")],
            "students": [("classroom_id", "TEXT NOT NULL DEFAULT 'default'"), ("archived", "INTEGER NOT NULL DEFAULT 0")],
            "auth_tokens": [("expires_at", "TEXT")],
            "sessions": [("is_mock", "INTEGER NOT NULL DEFAULT 0"), ("synced", "INTEGER NOT NULL DEFAULT 0"), ("words_json", "TEXT")],
            "story_sessions": [("is_mock", "INTEGER NOT NULL DEFAULT 0")],
            "story_attempts": [("is_mock", "INTEGER NOT NULL DEFAULT 0"), ("synced", "INTEGER NOT NULL DEFAULT 0")],
        }
        for table, columns in migrations.items():
            existing = {r[1] for r in cursor.execute(f"PRAGMA table_info({table})")}
            for column, definition in columns:
                if column not in existing:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS coaching_jobs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, arguments_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER DEFAULT 0, retry_after REAL DEFAULT 0, started_at REAL, last_error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sync_retries (kind TEXT, record_id TEXT, digest TEXT, attempts INTEGER DEFAULT 0, retry_after REAL DEFAULT 0, PRIMARY KEY(kind,record_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sync_received (source_id TEXT, kind TEXT, record_id TEXT, digest TEXT, payload_json TEXT, received_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(source_id,kind,record_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS classrooms (id TEXT PRIMARY KEY, join_code TEXT UNIQUE NOT NULL)")
        import secrets
        cursor.execute("INSERT OR IGNORE INTO app_metadata(key,value) VALUES ('source_id',?)", (secrets.token_hex(16),))
        cursor.execute("INSERT OR IGNORE INTO classrooms (id, join_code) VALUES ('default', ?)", (secrets.token_urlsafe(12),))
        cursor.execute("UPDATE auth_tokens SET expires_at = datetime(created_at, '+24 hours') WHERE expires_at IS NULL")
        cursor.execute("CREATE TABLE IF NOT EXISTS word_tip_cache (cache_key TEXT PRIMARY KEY, tip TEXT NOT NULL, syllables_json TEXT, source TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        # Old simulated attempts must not contribute to new reports.
        cursor.execute("UPDATE story_attempts SET is_mock=1 WHERE json_valid(result_json) AND json_extract(result_json, '$.mock') = 1")
        from core.security import verify_password
        legacy = cursor.execute("SELECT id, password_hash FROM users WHERE id='user-teacher-1'").fetchone()
        if legacy and verify_password("speakflow123", legacy["password_hash"]):
            cursor.execute("UPDATE users SET status='needs_setup' WHERE id=?", (legacy["id"],))
            cursor.execute("DELETE FROM auth_tokens WHERE user_id=?", (legacy["id"],))
        cursor.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)")
        if not cursor.execute("SELECT 1 FROM schema_migrations WHERE version=2").fetchone():
            cursor.execute("UPDATE story_sessions SET synced=0")
            cursor.execute("INSERT INTO schema_migrations(version) VALUES (2)")
        # Account-profile migration: additive, idempotent and history-preserving.
        classroom_columns = {r[1] for r in cursor.execute('PRAGMA table_info(classrooms)')}
        if 'kind' not in classroom_columns:
            cursor.execute("ALTER TABLE classrooms ADD COLUMN kind TEXT NOT NULL DEFAULT 'classroom'")
        if 'owner_user_id' not in classroom_columns:
            cursor.execute('ALTER TABLE classrooms ADD COLUMN owner_user_id TEXT')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY REFERENCES users(id),
            reader_mode TEXT NOT NULL CHECK(reader_mode IN ('child','adult','teacher','dyslexia')),
            reading_language TEXT NOT NULL DEFAULT 'en',
            interface_language TEXT NOT NULL DEFAULT 'en',
            native_language TEXT,
            translation_language TEXT,
            accessibility_json TEXT NOT NULL DEFAULT '{}',
            profile_completed INTEGER NOT NULL DEFAULT 0 CHECK(profile_completed IN (0,1)),
            version INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        # Existing users retain access; newly registered accounts explicitly start incomplete.
        cursor.execute('''INSERT OR IGNORE INTO user_profiles(user_id,reader_mode,profile_completed)
            SELECT id, CASE WHEN role='teacher' THEN 'teacher' ELSE 'child' END, 1 FROM users''')
        cursor.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (3)')
        cursor.execute("CREATE TABLE IF NOT EXISTS speech_evidence (record_kind TEXT NOT NULL, record_id TEXT NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(record_kind,record_id))")
        cursor.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (4)')

        # Compatibility read models feed dynamic attempts into existing reports.
        cursor.execute("DROP VIEW IF EXISTS report_sessions")
        cursor.execute("""CREATE VIEW report_sessions AS
            SELECT id, student_id, story_id, language, created_at, completed_at, synced, mode
            FROM story_sessions WHERE is_mock=0
            UNION ALL
            SELECT id, student_id, 'level-' || level, track, created_at, created_at, synced, 'recorded'
            FROM story_attempts WHERE is_mock=0""")
        cursor.execute("DROP VIEW IF EXISTS report_checkpoints")
        cursor.execute("""CREATE VIEW report_checkpoints AS
            SELECT cr.* FROM checkpoint_results cr JOIN story_sessions ss ON ss.id=cr.session_id WHERE ss.is_mock=0
            UNION ALL
            SELECT a.id, a.id, 'level-' || a.level, l.sentence,
                   json_extract(a.result_json, '$.transcript'), json_extract(a.result_json, '$.wpm'),
                   a.accuracy, a.passed, a.stars, json_extract(a.result_json, '$.words'),
                   json_extract(a.result_json, '$.hesitations'), json_extract(p.payload_json, '$.feedback_text'),
                   NULL, json_extract(p.payload_json, '$.comprehension_question'),
                   json_extract(p.payload_json, '$.practice_recommendation'), json_extract(p.payload_json, '$.teacher_note'),
                   json_extract(a.result_json, '$.stt_source'), json_extract(p.payload_json, '$.feedback_source'),
                   json_extract(a.result_json, '$.latency_ms'), a.created_at
            FROM story_attempts a LEFT JOIN story_levels l ON l.track=a.track AND l.level=a.level
            LEFT JOIN story_phase2 p ON p.attempt_id=a.id WHERE a.is_mock=0""")
        conn.commit()

if __name__ == "__main__":
    print("Initializing Database...")
    init_db()
    print(f"Database initialized at {DB_PATH}")
