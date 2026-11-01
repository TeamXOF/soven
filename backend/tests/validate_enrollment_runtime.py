"""Opt-in enrollment browser test against an isolated database and local HTTPS.

Requires a completed frontend production build, Node, Playwright and cryptography.
No real accounts, microphone, cloud API calls or production database are used.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import ipaddress
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.qa/runtime-validation'
sys.path.insert(0, str(ROOT / '.test-deps'))
sys.path.insert(0, str(ROOT / 'backend'))
WORK = tempfile.TemporaryDirectory(prefix='speakflow-enrollment-')
PRIVATE = Path(WORK.name)
os.environ.update(DATABASE_URL=str(PRIVATE / 'enrollment.db'), OFFLINE_MODE='1',
                  GOOGLE_API_KEY='', GOOGLE_API_KEYS='', GROQ_API_KEY='', ENABLE_MOCK_ANALYSIS='0')

import httpx
import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import FastAPI, Request
from fastapi.responses import Response
from database.schema import init_db, get_db_connection
from core.security import hash_password
from main import app


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    init_db()
    password = secrets.token_urlsafe(18)
    with get_db_connection() as conn:
        conn.execute("INSERT INTO classrooms(id,join_code) VALUES ('enrollment-ui','enrollment-ui-code')")
        conn.execute("INSERT INTO users(id,username,name,password_hash,role,status,classroom_id) VALUES ('ui-teacher','ui-teacher','Test teacher',?,'teacher','approved','enrollment-ui')", (hash_password(password),))
        conn.execute("INSERT INTO students(id,name,grade,level,classroom_id) VALUES ('existing-ui-profile','Existing child',5,'Level 2','enrollment-ui')")
        conn.commit()
    api_port, front_port, tls_port = free_port(), free_port(), free_port()
    api_url, front_url = f'http://127.0.0.1:{api_port}', f'http://127.0.0.1:{front_port}'
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=api_port, log_level='warning'))
    api_thread = threading.Thread(target=server.run, daemon=True)
    api_thread.start()
    node = os.getenv('VALIDATION_NODE') or shutil.which('node')
    if not node:
        raise RuntimeError('Set VALIDATION_NODE to the Node executable')
    front_log = (PRIVATE / 'frontend.log').open('w', encoding='utf-8')
    frontend = subprocess.Popen([node, 'node_modules/next/dist/bin/next', 'start', '--port', str(front_port)],
        cwd=ROOT / 'frontend', stdout=front_log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    @asynccontextmanager
    async def lifespan(proxy):
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            proxy.state.client = client
            yield

    proxy = FastAPI(lifespan=lifespan)

    @proxy.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    async def forward(request: Request, path: str):
        base = api_url if path.startswith(('api/', 'pipeline/')) or path == 'health' else front_url
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {'host', 'content-length', 'connection', 'accept-encoding'}}
        upstream = await proxy.state.client.request(request.method, base + '/' + path, params=request.query_params, headers=headers, content=await request.body())
        headers = {k: v for k, v in upstream.headers.items() if k.lower() not in {'content-length', 'transfer-encoding', 'connection', 'content-encoding'}}
        return Response(upstream.content, status_code=upstream.status_code, headers=headers)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Isolated enrollment test')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
            .sign(key, hashes.SHA256()))
    cert_path, key_path = PRIVATE / 'cert.pem', PRIVATE / 'key.pem'
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    tls_server = uvicorn.Server(uvicorn.Config(proxy, host='127.0.0.1', port=tls_port,
        ssl_certfile=str(cert_path), ssl_keyfile=str(key_path), log_level='warning'))
    tls_thread = threading.Thread(target=tls_server.run, daemon=True)
    tls_thread.start()
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            for _ in range(150):
                try:
                    ready = await client.get(front_url + '/login')
                    if ready.status_code == 200 and server.started and tls_server.started:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(.2)
            else:
                raise RuntimeError('Isolated enrollment servers did not start')
        env = dict(os.environ, VALIDATION_ENROLLMENT_URL=f'https://127.0.0.1:{tls_port}',
                   VALIDATION_TEACHER_PASSWORD=password, VALIDATION_ENROLLMENT_OUT=str(OUT))
        browser_script = os.getenv('VALIDATION_BROWSER_SCRIPT', 'validate_enrollment_ui.cjs')
        result = await asyncio.to_thread(subprocess.run,
            [node, str(ROOT / 'backend/tests' / browser_script)], env=env, capture_output=True, text=True, timeout=300)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        print(result.stdout, flush=True)
        if browser_script == 'validate_enrollment_ui.cjs':
            with get_db_connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM students WHERE classroom_id='enrollment-ui'").fetchone()[0] == 2
                assert conn.execute("SELECT student_id FROM users WHERE username='existing-ui-child'").fetchone()[0] == 'existing-ui-profile'
    finally:
        server.should_exit = True
        tls_server.should_exit = True
        frontend.terminate()
        frontend.wait(timeout=15)
        api_thread.join(timeout=15)
        tls_thread.join(timeout=15)
        front_log.close()
        WORK.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
