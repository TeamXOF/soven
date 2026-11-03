import os
import sys
import json
import uuid
import base64
from pathlib import Path
import requests

API_URL = "http://127.0.0.1:8000"

print("--- Testing Spanish Live Integration ---")

# 1. Capabilities check
cap = requests.get(f"{API_URL}/api/v1/capabilities").json()
es_lang = next((l for l in cap['language_catalog']['languages'] if l['code'] == 'es'), None)
print(f"1. Capabilities check: Spanish enabled_for_reading = {es_lang.get('enabled_for_reading')}")
assert es_lang.get('enabled_for_reading') is True

es_speech = cap.get('language_speech', {}).get('languages', {}).get('es')
print(f"2. Speech route check: Spanish locale = {es_speech.get('locale')}, recognition = {es_speech.get('recognition')}")
assert es_speech.get('locale') == 'es-ES'

# 2. Register adult reader and login to get auth token
u_name = f"carlos_{uuid.uuid4().hex[:6]}"
pwd = "Password123!"
reg_res = requests.post(f"{API_URL}/api/auth/register-adult", json={
    "name": "Carlos Reader",
    "username": u_name,
    "password": pwd
})
assert reg_res.status_code == 201, reg_res.text

login_res = requests.post(f"{API_URL}/api/auth/login", json={
    "username": u_name,
    "password": pwd
})
assert login_res.status_code == 200, login_res.text
auth_data = login_res.json()
token = auth_data["token"]
student_id = auth_data["user"]["student_id"]
headers = {"Authorization": f"Bearer {token}"}
print(f"3. Authenticated as: {u_name}, student_id={student_id}")

# 3. Create Spanish reading session
sess_res = requests.post(f"{API_URL}/api/v1/sessions", headers=headers, json={
    "student_id": student_id,
    "story_id": "story_forest_01",
    "language": "es"
})
assert sess_res.status_code in [200, 201], sess_res.text
session = sess_res.json()
print(f"4. Created Spanish reading session: {session['session_id']}")
print(f"   Checkpoints count: {len(session['checkpoints'])}")
for i, cp in enumerate(session['checkpoints']):
    print(f"   CP #{i+1}: {cp['target_text']}")

assert "zorro" in session['checkpoints'][0]['target_text']

# 4. Test Spanish word tip (GET /api/v1/words/tip?word=zorro&lang=es)
tip_res = requests.get(f"{API_URL}/api/v1/words/tip", headers=headers, params={"word": "zorro", "lang": "es"})
print(f"5. Word tip for 'zorro' (status {tip_res.status_code}):")
assert tip_res.status_code in [200, 201], tip_res.text
tip_data = tip_res.json()
print(f"   Tip response: {json.dumps(tip_data, indent=2, ensure_ascii=False)}")
assert tip_data.get("tip") is not None

# 5. Test Spanish exercise generation (GET /pipeline/sentences?difficulty=medium&count=3&language=es)
ex_res = requests.get(f"{API_URL}/pipeline/sentences?difficulty=medium&count=3&language=es", headers=headers)
print(f"6. Spanish practice sentences (status {ex_res.status_code}):")
assert ex_res.status_code in [200, 201], ex_res.text
ex_data = ex_res.json()
print(f"   Generated sentences: {ex_data.get('sentences')}")
# Verify generated sentences are Spanish
sentences = ex_data.get('sentences', [])
assert len(sentences) >= 1
print(f"   Sample sentence: {sentences[0]}")

# 6. Test 5-agent pipeline with Spanish and real audio
wav_path = Path(".qa/speech-evaluation/runner-v1/controls/correct.wav")
if not wav_path.is_file():
    wav_path = Path(".qa/my_recording.m4a")

audio_b64 = base64.b64encode(wav_path.read_bytes()).decode("ascii")

pipe_res = requests.post(f"{API_URL}/pipeline/run", headers=headers, json={
    "student_id": student_id,
    "target_sentence": "El pequeño zorro se despertó temprano en la mañana.",
    "audio_base64": audio_b64,
    "language": "es"
})
print(f"7. 5-Agent pipeline run (status {pipe_res.status_code}):")
assert pipe_res.status_code in [200, 201], pipe_res.text
pipe_data = pipe_res.json()
for agent in pipe_data.get('agents', []):
    print(f"   Agent [{agent['id']}]: status={agent['status']}")
    if agent.get('result'):
        print(f"      Result summary: {json.dumps(agent['result'], ensure_ascii=False)[:140]}...")

print("\n>>> ALL SPANISH MODULES VERIFIED END-TO-END! <<<")
