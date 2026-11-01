"""Acknowledged snapshot sync for all engines, with persistent retry state."""
import hashlib
import json
import os
import threading
import time
from urllib.parse import urlparse
import requests
from core.config import settings
from database.schema import get_db_connection
from services.stt import network_available

TABLES = {"classic": "sessions", "checkpoint": "story_sessions", "dynamic": "story_attempts"}
_push_lock = threading.Lock()


def snapshot(conn, kind, row):
    payload = dict(row)
    payload.pop("synced", None)
    if kind == "checkpoint":
        payload["checkpoints"] = [dict(r) for r in conn.execute("SELECT * FROM checkpoint_results WHERE session_id=? ORDER BY checkpoint_id", (row["id"],))]
    elif kind == "classic":
        result = conn.execute("SELECT * FROM diagnoses WHERE session_id=?", (row["id"],)).fetchone()
        payload["diagnosis"] = dict(result) if result else None
    elif kind == "dynamic":
        result = conn.execute("SELECT payload_json FROM story_phase2 WHERE attempt_id=?", (row["id"],)).fetchone()
        payload["feedback"] = json.loads(result[0]) if result else None
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return payload, hashlib.sha256(encoded.encode()).hexdigest()


def get_queued_count():
    with get_db_connection() as conn:
        return sum(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE synced=0 AND is_mock=0").fetchone()[0] for table in TABLES.values())


def push_queued():
    url = settings.CLOUD_SYNC_URL
    secret = os.getenv("SYNC_SHARED_SECRET", "")
    result = {"synced_count": 0, "failed_count": 0, "queued": get_queued_count(), "note": ""}
    if os.getenv("OFFLINE_MODE") == "1":
        result["note"] = "Offline mode is enabled. Snapshots remain queued locally."
        return result
    if not url or len(secret) < 32:
        result["note"] = "Configure CLOUD_SYNC_URL and a SYNC_SHARED_SECRET of at least 32 characters. Data remains local."
        return result
    parsed = urlparse(url)
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        result["note"] = "Remote sync requires HTTPS."
        return result
    if not _push_lock.acquire(blocking=False):
        result["note"] = "Sync already running."
        return result
    try:
        with get_db_connection() as conn:
            source_id = conn.execute("SELECT value FROM app_metadata WHERE key='source_id'").fetchone()[0]
            queued = [(kind, dict(r)) for kind, table in TABLES.items() for r in conn.execute(f"SELECT * FROM {table} WHERE synced=0 AND is_mock=0 LIMIT 100")]
        for kind, row in queued:
            with get_db_connection() as conn:
                payload, digest = snapshot(conn, kind, row)
                retry = conn.execute("SELECT * FROM sync_retries WHERE kind=? AND record_id=?", (kind, row["id"])).fetchone()
            if retry and retry["digest"] == digest and retry["retry_after"] > time.time():
                continue
            try:
                packet = {"source_id": source_id, "kind": kind, "record_id": row["id"], "digest": digest, "payload": payload}
                response = requests.post(url, json=packet, headers={"Authorization": f"Bearer {secret}"}, timeout=(3, 8))
                response.raise_for_status()
                ack = response.json()
                if ack.get("record_id") != row["id"] or ack.get("digest") != digest:
                    raise ValueError("Unacknowledged snapshot")
                with get_db_connection() as conn:
                    current = conn.execute(f"SELECT * FROM {TABLES[kind]} WHERE id=?", (row["id"],)).fetchone()
                    if current and snapshot(conn, kind, current)[1] == digest:
                        conn.execute(f"UPDATE {TABLES[kind]} SET synced=1 WHERE id=?", (row["id"],))
                        result["synced_count"] += 1
                    conn.execute("DELETE FROM sync_retries WHERE kind=? AND record_id=?", (kind, row["id"]))
                    conn.commit()
            except Exception:
                attempts = (retry["attempts"] if retry and retry["digest"] == digest else 0) + 1
                with get_db_connection() as conn:
                    conn.execute("INSERT OR REPLACE INTO sync_retries VALUES (?,?,?,?,?)", (kind, row["id"], digest, attempts, time.time()+min(3600, 15*2**min(attempts,8))))
                    conn.commit()
                result["failed_count"] += 1
    finally:
        _push_lock.release()
    result["queued"] = get_queued_count()
    return result


class SyncWatcher(threading.Thread):
    daemon = True

    def __init__(self):
        super().__init__(name="sync-watcher")
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.wait(settings.SYNC_INTERVAL_S):
            try:
                if settings.CLOUD_SYNC_URL and os.getenv("OFFLINE_MODE") != "1" and network_available():
                    push_queued()
            except Exception:
                pass  # Retry on the next interval, including after initial failures.

    def stop(self):
        self._stop_event.set()


def start_sync_watcher():
    watcher = SyncWatcher()
    watcher.start()
    return watcher
