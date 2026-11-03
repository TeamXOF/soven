"""Stateless, server-configured JSON reasoning. No automatic provider switching."""
import asyncio
import json
import math
import os
import re
import time
from urllib.parse import urlsplit

import requests
from core.config import settings

MAX_REQUEST_BYTES = 96 * 1024
MAX_RESPONSE_BYTES = 128 * 1024


class ModelResult(dict):
    """Provenance cannot be supplied or overwritten by generated JSON fields."""
    def __init__(self, data, provider, model):
        super().__init__(data)
        self.provider = provider
        self.model = model


def selected_provider():
    provider = os.getenv('REASONING_PROVIDER', 'meta' if os.getenv('SPEAKFLOW_LLM_BASE_URL') else 'meta').strip().lower()
    if provider not in {'google', 'meta', 'chat_completions'}:
        raise RuntimeError('Unknown reasoning provider')
    return provider


def model_candidates(primary, fallback):
    # Google keeps its existing model alias retry. Other providers never receive
    # Google identifiers or silently transfer observations to a different service.
    return list(dict.fromkeys([primary, fallback])) if os.getenv('REASONING_PROVIDER', 'google').strip().lower() == 'google' else [primary]


def result_source(result):
    return {'google': 'gemini', 'meta': 'meta', 'chat_completions': 'chat_completions'}.get(
        getattr(result, 'provider', None), 'model_unknown')


def _endpoint(base):
    try:
        url = urlsplit(base)
        port = url.port
    except ValueError:
        raise RuntimeError('Invalid reasoning base URL') from None
    loopback = url.hostname in {'localhost', '127.0.0.1', '::1'}
    if (not url.hostname or url.username is not None or url.password is not None
            or url.query or url.fragment or (port is not None and not 1 <= port <= 65535)
            or not (url.scheme == 'https' or (url.scheme == 'http' and loopback))):
        raise RuntimeError('Reasoning base URL requires HTTPS or loopback HTTP')
    return base.rstrip('/') + '/chat/completions'


def _post_json(url, headers, body, timeout):
    encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_REQUEST_BYTES:
        raise RuntimeError('Reasoning request exceeds size limit')
    start = time.monotonic()
    try:
        with requests.post(url, headers={**headers, 'Content-Type': 'application/json'},
                           data=encoded, timeout=(min(3, timeout), timeout),
                           stream=True, allow_redirects=False) as response:
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f'Reasoning provider returned HTTP {response.status_code}')
            chunks, size = [], 0
            for chunk in response.iter_content(chunk_size=4096):
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise RuntimeError('Reasoning response exceeds size limit')
                if time.monotonic() - start > timeout:
                    raise RuntimeError('Reasoning response deadline exceeded')
                chunks.append(chunk)
            result = json.loads(b''.join(chunks))
    except requests.RequestException:
        # Exception URLs/bodies can contain credentials, prompts or personal data.
        raise RuntimeError('Reasoning provider transport failed') from None
    except (ValueError, UnicodeError):
        raise RuntimeError('Reasoning provider returned invalid JSON') from None
    if not isinstance(result, dict):
        raise RuntimeError('Reasoning provider returned an invalid envelope')
    return result


def generate_json_sync(prompt: str, payload: dict, model: str, timeout: float = 10,
                       schema: dict | None = None) -> dict:
    if os.getenv('OFFLINE_MODE', '0') == '1':
        raise RuntimeError('Cloud reasoning disabled in offline mode')
    if not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ValueError('Reasoning timeout must be within 30 seconds')
    provider = selected_provider()
    if provider == 'google':
        key = next((k.strip() for k in settings.active_gemini_key.split(',') if k.strip()), '')
        if not key:
            raise RuntimeError('Cloud reasoning is not configured')
        if not re.fullmatch(r'[A-Za-z0-9._-]+', model):
            raise ValueError('Invalid model identifier')
        body = {'systemInstruction': {'parts': [{'text': prompt}]},
                'contents': [{'role': 'user', 'parts': [{'text': json.dumps(payload, ensure_ascii=False)}]}],
                'generationConfig': {'responseMimeType': 'application/json', 'maxOutputTokens': 2048}}
        envelope = _post_json(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            {'x-goog-api-key': key}, body, timeout)
        candidates = envelope.get('candidates') or []
        candidate = candidates[0] if candidates else {}
        if candidate.get('finishReason') not in (None, 'STOP'):
            raise RuntimeError('Reasoning output was not completed')
        text = ''.join(p.get('text', '') for p in candidate.get('content', {}).get('parts', [])
                       if not p.get('thought'))
    else:
        key = os.getenv('REASONING_API_KEY', '').strip()
        model = os.getenv('REASONING_MODEL', '').strip() or ('muse-spark-1.3' if provider == 'meta' else 'muse-glimmer')
        if not model or len(model) > 128 or any(ord(c) < 32 for c in model):
            raise RuntimeError('Reasoning model must be configured')
        if not schema:
            raise RuntimeError('Structured reasoning requires an output schema')
        base = os.getenv('SPEAKFLOW_LLM_BASE_URL', os.getenv('REASONING_BASE_URL', 'https://api.meta.ai/v1' if provider == 'meta' else '')).strip()
        endpoint = _endpoint(base)
        if (provider == 'meta' or urlsplit(endpoint).scheme == 'https') and not key:
            # Allow keyless access for local or test mock endpoints, otherwise require key
            if not urlsplit(endpoint).hostname in {'localhost', '127.0.0.1', '::1'}:
                if os.getenv('REASONING_ACCESS_CONFIRMED', '0') != '1' and not key:
                    raise RuntimeError('Reasoning API key must be configured')
        # Standard mode (muse-spark-1.3 or muse-glimmer), never -contributor mode
        # Passes reasoning_effort="low" (NEVER "none", stop, or logit_bias which cause HTTP 400 on Muse Spark)
        body = {
            'model': model,
            'messages': [
                {'role': 'developer' if provider == 'meta' else 'system', 'content': prompt},
                {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
            ],
            'reasoning_effort': 'low',
            'response_format': {
                'type': 'json_schema',
                'json_schema': {'name': 'soven_reading_guidance', 'schema': schema}
            },
            'max_completion_tokens': 2048,
            'stream': False
        }
        envelope = _post_json(endpoint, {'Authorization': 'Bearer ' + key} if key else {}, body, timeout)
        choices = envelope.get('choices') or []
        choice = choices[0] if choices else {}
        message = choice.get('message') or {}
        if choice.get('finish_reason') != 'stop' or message.get('refusal') or message.get('tool_calls'):
            raise RuntimeError('Reasoning output was refused or not completed')
        text = message.get('content')
    try:
        result = json.loads(text)
    except (TypeError, ValueError):
        raise RuntimeError('Model returned invalid JSON content') from None
    if not isinstance(result, dict):
        raise RuntimeError('Model must return a JSON object')
    return ModelResult(result, provider, model)


async def generate_json(prompt: str, payload: dict, model: str, timeout: float = 10,
                        schema: dict | None = None) -> dict:
    # Cancels the await, not an already-running HTTP thread. Connect/read timeouts,
    # byte limits and a checked read deadline also bound transport work.
    return await asyncio.wait_for(asyncio.to_thread(
        generate_json_sync, prompt, payload, model, timeout, schema), timeout + 1)
