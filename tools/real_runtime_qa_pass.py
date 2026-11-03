"""
SOVEN Real Runtime QA Audit Script
Executes steps 3, 4, 5 in isolated process memory without disk credential leakage.
"""
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / ".qa"
TEMP_DB = QA_DIR / "qa_audit_runtime.db"
WAV_FIXTURE = QA_DIR / "speech-evaluation" / "runner-v1" / "controls" / "correct.wav"
UPLOADED_ENV = Path(r"C:/Users/Ace/.gemini/antigravity/brain/8d61613b-fa0f-4d28-aec5-079e5d8811c3/.user_uploaded/media_1793640312927_ac7a9998.env")


def load_memory_env():
    # 1. Base backend env
    backend_env = dotenv_values(ROOT / "backend" / ".env")
    # 2. Uploaded speakflow env
    uploaded_env = dotenv_values(UPLOADED_ENV) if UPLOADED_ENV.is_file() else {}

    # Merge into a clean process environment
    merged = dict(os.environ)
    for k, v in backend_env.items():
        if v is not None:
            merged[k] = v
    for k, v in uploaded_env.items():
        if v is not None and v != "":
            merged[k] = v

    # Override for strict QA audit
    merged["DATABASE_URL"] = str(TEMP_DB.resolve())
    merged["CLOUD_SYNC_URL"] = ""
    merged["SYNC_SHARED_SECRET"] = ""
    merged["HOST"] = "127.0.0.1"
    merged["PORT"] = "8000"
    merged["OFFLINE_MODE"] = "0"
    merged["ENABLE_MOCK_ANALYSIS"] = "0"
    merged["STT_MODE"] = "auto"
    merged["REASONING_PROVIDER"] = backend_env.get("REASONING_PROVIDER", "chat_completions")
    return merged


def run_audit():
    env = load_memory_env()

    # Pre-cleanup temporary database
    if TEMP_DB.is_file():
        try:
            TEMP_DB.unlink()
        except Exception:
            pass

    google_configured = bool(env.get("GOOGLE_API_KEYS") or env.get("GEMINI_API_KEY_DEMO"))
    groq_configured = bool(env.get("GROQ_API_KEY"))

    print(f"[PREFLIGHT] google_configured: {google_configured}, groq_configured: {groq_configured}")
    print(f"[PREFLIGHT] temp_db: {TEMP_DB}")
    print(f"[PREFLIGHT] wav_fixture exists: {WAV_FIXTURE.is_file()}")

    # Launch backend server via python -m uvicorn main:app
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"],
        cwd=str(ROOT / "backend"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    import requests

    results = {
        "preflight": {
            "google_key_configured": google_configured,
            "groq_key_configured": groq_configured,
            "temp_db_path": str(TEMP_DB.name),
            "fixture_exists": WAV_FIXTURE.is_file()
        },
        "endpoints": {},
        "adult_journey": {},
        "security_isolation": {},
        "live_speech_service": {},
        "live_feedback_service": {},
        "errors": []
    }

    try:
        # Wait for server
        base_url = "http://127.0.0.1:8000"
        ready = False
        for _ in range(60):
            try:
                r = requests.get(f"{base_url}/health", timeout=1)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.5)

        if not ready:
            raise RuntimeError("Backend server failed to start within 30s")

        print("[SERVER] Backend ready on http://127.0.0.1:8000")

        # 1. Health check
        r_health = requests.get(f"{base_url}/health", timeout=5)
        results["endpoints"]["health"] = {
            "status_code": r_health.status_code,
            "data": r_health.json()
        }

        # 2. Capabilities check
        r_cap = requests.get(f"{base_url}/api/v1/capabilities", timeout=5)
        cap_json = r_cap.json()
        results["endpoints"]["capabilities"] = {
            "status_code": r_cap.status_code,
            "schema_version": cap_json.get("schema_version"),
            "providers_count": len(cap_json.get("providers", [])),
            "enabled_reading_languages": [
                lang for lang, policy in cap_json.get("language_speech", {}).get("languages", {}).items()
            ],
            "notice_present": bool(cap_json.get("notice"))
        }

        # 3. Adult Registration & Login (User A)
        ts = int(time.time())
        username_a = f"adult_auditor_qa_{ts}"
        reg_payload = {
            "name": "Audit Adult Reader",
            "username": username_a,
            "password": "ValidAuditPassword123!"
        }
        r_reg = requests.post(f"{base_url}/api/auth/register-adult", json=reg_payload, timeout=5)
        results["adult_journey"]["registration"] = {
            "status_code": r_reg.status_code,
            "body": r_reg.json()
        }

        r_login = requests.post(f"{base_url}/api/auth/login", json={
            "username": username_a,
            "password": "ValidAuditPassword123!"
        }, timeout=5)
        login_data = r_login.json()
        token_a = login_data.get("token")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        results["adult_journey"]["login"] = {
            "status_code": r_login.status_code,
            "user_role": login_data.get("user", {}).get("role"),
            "reader_mode": login_data.get("user", {}).get("reader_mode"),
            "profile_completed": login_data.get("user", {}).get("profile_completed")
        }

        # 4. Profile Read & Update
        r_prof = requests.get(f"{base_url}/api/auth/profile", headers=headers_a, timeout=5)
        prof_data = r_prof.json().get("profile", {})
        results["adult_journey"]["initial_profile"] = {
            "status_code": r_prof.status_code,
            "version": prof_data.get("version"),
            "profile_completed": prof_data.get("profile_completed")
        }

        r_prof_update = requests.patch(f"{base_url}/api/auth/profile", headers=headers_a, json={
            "expected_version": prof_data.get("version", 1),
            "native_language": "en",
            "reading_language": "en",
            "interface_language": "en",
            "complete_profile": True,
            "accessibility": {"larger_text": True}
        }, timeout=5)
        updated_prof = r_prof_update.json().get("profile", {})
        results["adult_journey"]["updated_profile"] = {
            "status_code": r_prof_update.status_code,
            "version": updated_prof.get("version"),
            "profile_completed": updated_prof.get("profile_completed"),
            "native_language": updated_prof.get("native_language"),
            "accessibility_larger_text": updated_prof.get("accessibility", {}).get("larger_text")
        }

        # 5. Load Story Catalogue (English and Urdu)
        r_cat_en = requests.get(f"{base_url}/api/v1/stories?language=en", headers=headers_a, timeout=5)
        r_cat_ur = requests.get(f"{base_url}/api/v1/stories?language=ur", headers=headers_a, timeout=5)
        results["adult_journey"]["catalogue"] = {
            "english_status": r_cat_en.status_code,
            "english_stories_count": len(r_cat_en.json()),
            "first_story_id": r_cat_en.json()[0]["id"] if r_cat_en.json() else None,
            "urdu_status": r_cat_ur.status_code,
            "urdu_stories_count": len(r_cat_ur.json())
        }

        # 6. Create Reading Session
        story_id = "story_forest_01"
        r_sess = requests.post(f"{base_url}/api/v1/sessions", headers=headers_a, json={
            "story_id": story_id,
            "language": "en"
        }, timeout=5)
        sess_data = r_sess.json()
        session_id = sess_data.get("session_id")
        results["adult_journey"]["session_creation"] = {
            "status_code": r_sess.status_code,
            "session_id_prefix": session_id[:8] if session_id else None,
            "story_id": sess_data.get("story_id"),
            "checkpoints_count": len(sess_data.get("checkpoints", []))
        }

        # 7. Security Isolation: Register User B and verify cross-account isolation
        username_b = f"second_auditor_qa_{ts}"
        reg_b = requests.post(f"{base_url}/api/auth/register-adult", json={
            "name": "Second Reader",
            "username": username_b,
            "password": "ValidAuditPassword123!"
        }, timeout=5)
        login_b = requests.post(f"{base_url}/api/auth/login", json={
            "username": username_b,
            "password": "ValidAuditPassword123!"
        }, timeout=5)
        token_b = login_b.json().get("token")
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # B tries to access A's session
        r_b_access = requests.get(f"{base_url}/api/v1/sessions/{session_id}", headers=headers_b, timeout=5)
        # B lists sessions (should be empty for B)
        r_b_list = requests.get(f"{base_url}/api/v1/sessions", headers=headers_b, timeout=5)
        b_sessions = r_b_list.json() if r_b_list.status_code == 200 else []
        session_ids_for_b = [s.get("id") or s.get("session_id") for s in b_sessions]

        # Unauthorized access without token
        r_no_auth = requests.get(f"{base_url}/api/v1/sessions/{session_id}", timeout=5)
        # Bad token
        r_bad_auth = requests.get(f"{base_url}/api/v1/sessions/{session_id}", headers={"Authorization": "Bearer bad-token-xyz"}, timeout=5)

        results["security_isolation"] = {
            "cross_user_access_status": r_b_access.status_code,
            "cross_user_isolated": r_b_access.status_code in (403, 404),
            "session_leak_in_list": session_id in session_ids_for_b,
            "unauthorized_no_token_status": r_no_auth.status_code,
            "unauthorized_bad_token_status": r_bad_auth.status_code
        }

        # 8. Live Configured-Service Check: analyze synthetic correct.wav
        checkpoint_id = "cp_1"
        t0 = time.monotonic()
        with open(WAV_FIXTURE, "rb") as audio_f:
            files = {"audio": ("correct.wav", audio_f, "audio/wav")}
            data = {"checkpoint_id": checkpoint_id}
            r_analyze = requests.post(
                f"{base_url}/api/v1/sessions/{session_id}/analyze",
                headers=headers_a,
                data=data,
                files=files,
                timeout=30
            )
        analyze_latency = round((time.monotonic() - t0) * 1000, 1)

        analyze_data = r_analyze.json() if r_analyze.status_code == 200 else {}
        evidence = analyze_data.get("speech_evidence") or {}

        results["live_speech_service"] = {
            "http_status": r_analyze.status_code,
            "latency_ms": analyze_latency,
            "stt_source": analyze_data.get("stt_source"),
            "accuracy": analyze_data.get("accuracy"),
            "wpm": analyze_data.get("wpm"),
            "passed": analyze_data.get("passed"),
            "evidence": {
                "origin": evidence.get("origin"),
                "language": evidence.get("language"),
                "provider": evidence.get("provider"),
                "engine": evidence.get("engine"),
                "fallback_reason": evidence.get("fallback_reason"),
                "word_timing": evidence.get("word_timing"),
                "recognition_confidence": evidence.get("recognition_confidence"),
                "confidence_basis": evidence.get("confidence_basis"),
                "pause_assessment": evidence.get("pause_assessment"),
                "quality_validated": evidence.get("quality_validated")
            }
        }

        # 9. Poll Phase-Two Feedback
        feedback_received = False
        feedback_data = {}
        for poll_round in range(15):
            time.sleep(1)
            r_fb = requests.get(f"{base_url}/api/v1/sessions/{session_id}/feedback/{checkpoint_id}", headers=headers_a, timeout=5)
            if r_fb.status_code == 200:
                fb = r_fb.json()
                if fb.get("feedback_text"):
                    feedback_received = True
                    feedback_data = fb
                    break

        results["live_feedback_service"] = {
            "feedback_received": feedback_received,
            "polls_taken": poll_round + 1,
            "feedback_source": feedback_data.get("feedback_source"),
            "has_feedback_text": bool(feedback_data.get("feedback_text")),
            "has_comprehension_question": bool(feedback_data.get("comprehension_question")),
            "has_practice_recommendation": bool(feedback_data.get("practice_recommendation")),
            "teacher_note_present": bool(feedback_data.get("teacher_note"))
        }

    except Exception as exc:
        results["errors"].append(str(exc))
        print(f"[ERROR] Exception during QA: {exc}")
    finally:
        print("[CLEANUP] Stopping server process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        # Delete temp db if created
        if TEMP_DB.is_file():
            try:
                TEMP_DB.unlink()
                # Also delete wal/shm if present
                for extra in [Path(str(TEMP_DB) + "-wal"), Path(str(TEMP_DB) + "-shm")]:
                    if extra.is_file():
                        extra.unlink()
                print("[CLEANUP] Cleaned up temporary database.")
            except Exception as e:
                print(f"[CLEANUP WARNING] Failed to delete temp db: {e}")

    out_file = QA_DIR / "real_runtime_qa_output.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[DONE] Wrote audit output to {out_file}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_audit()
