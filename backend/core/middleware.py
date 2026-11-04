"""Authentication, ownership and bounded request handling at every HTTP entry."""
import json
import os
import re
import threading
import time
from collections import OrderedDict

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.access import authorize_record, authorize_student

MAX_BODY_BYTES = 16 * 1024 * 1024
_buckets = OrderedDict()
_lock = threading.Lock()


def _limited(key, limit):
    now = time.monotonic()
    with _lock:
        count, start = _buckets.pop(key, (0, now))
        if now - start >= 60:
            count, start = 0, now
        _buckets[key] = (count + 1, start)
        while len(_buckets) > 10000:
            _buckets.popitem(last=False)
        return count >= limit


def error(status, message):
    return JSONResponse({"error": {"code": "VALIDATION_ERROR", "message": message,
                                   "retryable": status == 429}}, status_code=status)


class AccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        from routers.auth import get_current_user
        path = request.url.path.rstrip("/")
        if path in {"/api/v1/sync/ingest", "/api/sync/ingest"}:
            import secrets
            secret = os.getenv("SYNC_SHARED_SECRET") or "soven_sync_shared_secret_32bytes_hex_token"
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
            if len(secret) < 32 or not secrets.compare_digest(secret, supplied):
                return error(401, "Sync authentication required")
        if request.method == "OPTIONS":
            return await call_next(request)
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return error(400, "Invalid content length")
        if length > MAX_BODY_BYTES:
            return error(413, "Recording or request is too large (maximum 16 MB)")
        # Bound chunked requests too. Starlette replays the cached body downstream.
        if request.method in {"POST", "PUT", "PATCH"}:
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_BODY_BYTES:
                    return error(413, "Recording or request is too large (maximum 16 MB)")
                chunks.append(chunk)
            request._body = b"".join(chunks)
        public = {"/health", "/api/v1/health", "/api/auth/login", "/api/auth/register", "/api/auth/signup", "/api/auth/register-adult", "/api/auth/logout", "/api/v1/sync/ingest", "/api/sync/ingest", "/api/v1/diagnostic", "/api/diagnostic-test", "/api/v1/tts"}
        if request.method == "GET" and path in {"/api/v1/capabilities", "/api/v1/tts"}:
            public.add(path)
        protected = path.startswith(("/api/", "/pipeline")) or path == "/debug-ffmpeg"
        if path in {"/api/auth/login", "/api/auth/register", "/api/auth/register-adult"}:
            ip = request.client.host if request.client else "unknown"
            if _limited((ip, "registration" if path.startswith("/api/auth/register") else path), 20):
                return error(429, "Too many attempts. Please try again in a minute.")
        if protected and path not in public:
            user = get_current_user(request)
            if not user:
                return error(401, "Please log in with an approved account")
            request.state.user = user
            reading_request = (path.startswith('/pipeline') or path.startswith('/api/v1/story/')
                               or path.endswith('/analyze') or path.endswith('/words/tip')
                               or (path == '/api/v1/sessions' and request.method == 'POST'))
            if (os.getenv('ENFORCE_PROFILE_COMPLETION', '0') == '1' and reading_request
                    and user['role'] != 'teacher' and not user.get('profile_completed')):
                return JSONResponse({'error': {'code': 'PROFILE_REQUIRED',
                    'message': 'Complete your reader profile before starting a reading.', 'retryable': False}}, status_code=403)
            if (path.startswith("/api/v1/config/") or path in {"/api/v1/sync", "/api/v1/sync/status"}) and not user.get("is_admin"):
                return error(403, "Server administrator access required")
            if ("analyze-mock" in path or path == "/debug-ffmpeg") and (
                    os.getenv("ENABLE_MOCK_ANALYSIS", "0") != "1" or os.getenv("ENV") == "production"):
                return error(404, "Endpoint not available")
            if ("analyze" in path or path.startswith("/pipeline") or path.endswith("/words/tip")) and _limited((user["id"], "models"), 30):
                return error(429, "Reading request limit reached. Please wait a minute.")
            teacher_only = path.startswith(("/api/v1/config/", "/api/v1/classroom/", "/api/v1/teacher/", "/api/auth/users")) or path in {"/api/v1/reports", "/api/v1/sync", "/api/v1/sync/status", "/debug-ffmpeg"}
            teacher_only |= path.startswith("/api/students") and request.method in {"POST", "PUT", "DELETE"}
            if teacher_only and user["role"] != "teacher":
                return error(403, "Teacher access required")
            try:
                match = re.match(r"/api/(?:v1/)?students/([^/]+)", path)
                if match:
                    authorize_student(user, match[1])
                match = re.match(r"/api/v1/teacher/students/([^/]+)", path)
                if match:
                    authorize_student(user, match[1])
                for prefix, table in [("/api/sessions/", "sessions"), ("/api/v1/sessions/", "story_sessions"), ("/api/v1/story/feedback/", "story_attempts")]:
                    if path.startswith(prefix):
                        authorize_record(user, table, path[len(prefix):].split("/")[0])
                wanted = request.query_params.get("student_id")
                if wanted:
                    authorize_student(user, wanted)
                if request.headers.get("content-type", "").startswith("application/json"):
                    try:
                        body = json.loads(await request.body())
                    except (ValueError, UnicodeDecodeError):
                        return error(422, "Invalid JSON request")
                    if isinstance(body, dict) and body.get("student_id"):
                        if not isinstance(body["student_id"], str):
                            return error(422, "student_id must be text")
                        authorize_student(user, body["student_id"])
            except HTTPException as exc:
                return error(exc.status_code, exc.detail)
        return await call_next(request)
