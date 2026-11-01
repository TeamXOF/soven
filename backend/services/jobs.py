"""Persistent coaching jobs; failures/restarts do not strand feedback forever."""
import asyncio
import json
import threading
import time

from database.schema import get_db_connection


def enqueue(kind, key, arguments):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO coaching_jobs(id,kind,arguments_json,status,retry_after) VALUES (?,?,?,'pending',0)", (key,kind,json.dumps(arguments,ensure_ascii=False)))
        conn.commit()
    return key


def run_job(key):
    with get_db_connection() as conn:
        conn.execute("UPDATE coaching_jobs SET status='pending' WHERE id=? AND status='running' AND started_at<?", (key,time.time()-120))
        claimed=conn.execute("UPDATE coaching_jobs SET status='running',started_at=?,attempts=attempts+1 WHERE id=? AND status='pending' AND retry_after<=?", (time.time(),key,time.time())).rowcount
        row=conn.execute("SELECT * FROM coaching_jobs WHERE id=?",(key,)).fetchone()
        conn.commit()
    if not claimed:
        return
    try:
        arguments=json.loads(row['arguments_json'])
        if row['kind']=='dynamic':
            from routers.story_mode import _run_phase2
            _run_phase2(*arguments)
        elif row['kind']=='checkpoint':
            from routers.v1 import _run_phase2
            asyncio.run(_run_phase2(*arguments))
        else:
            raise ValueError('Unknown coaching job')
        with get_db_connection() as conn:
            conn.execute("UPDATE coaching_jobs SET status='done',last_error=NULL WHERE id=?",(key,))
            conn.commit()
    except Exception:
        with get_db_connection() as conn:
            conn.execute("UPDATE coaching_jobs SET status='pending',last_error='Coaching will retry',retry_after=? WHERE id=?", (time.time()+min(300,5*2**min(row['attempts'],6)),key))
            conn.commit()


class JobWatcher(threading.Thread):
    daemon=True

    def __init__(self):
        super().__init__(name='coaching-jobs')
        self._stop_event=threading.Event()

    def run(self):
        while not self._stop_event.wait(5):
            try:
                with get_db_connection() as conn:
                    rows=conn.execute("SELECT id FROM coaching_jobs WHERE (status='pending' AND retry_after<=?) OR (status='running' AND started_at<?) ORDER BY created_at LIMIT 10",(time.time(),time.time()-120)).fetchall()
                for row in rows:
                    if self._stop_event.is_set(): return
                    run_job(row['id'])
            except Exception:
                continue

    def stop(self):
        self._stop_event.set()
