"""Stateless JSON generation: per-call credentials, bounded time and output."""
import asyncio
import json
import os
import re
import requests

from core.config import settings


def generate_json_sync(prompt: str, payload: dict, model: str, timeout: float = 10) -> dict:
    if os.getenv("OFFLINE_MODE", "0") == "1":
        raise RuntimeError("Cloud reasoning disabled in offline mode")
    key = next((k.strip() for k in settings.active_gemini_key.split(",") if k.strip()), "")
    if not key:
        raise RuntimeError("Cloud reasoning is not configured")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ValueError("Invalid model identifier")
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key},
        json={"systemInstruction": {"parts": [{"text": prompt}]},
              "contents": [{"role": "user", "parts": [{"text": json.dumps(payload, ensure_ascii=False)}]}],
              "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 2048}},
        timeout=(min(3, timeout), timeout))
    if response.status_code >= 400:
        # Provider bodies may contain request content; keep them out of logs/UI.
        raise RuntimeError(f"Reasoning provider returned HTTP {response.status_code}")
    parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("Model must return a JSON object")
    return result


async def generate_json(prompt: str, payload: dict, model: str, timeout: float = 10) -> dict:
    return await asyncio.wait_for(asyncio.to_thread(generate_json_sync, prompt, payload, model, timeout), timeout + 1)
