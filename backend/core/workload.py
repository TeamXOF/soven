"""Bound CPU/audio jobs independently of FastAPI's HTTP event loop."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from functools import partial
from threading import BoundedSemaphore

from fastapi import HTTPException
from services.stt import NoSpeechError

_audio_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="reading-audio")
_slots = BoundedSemaphore(8)


async def run_audio(function, *args):
    if not _slots.acquire(blocking=False):
        raise HTTPException(503, "The reading server is busy. Please retry shortly.")
    try:
        context = copy_context()
        future = _audio_pool.submit(context.run, partial(function, *args))
    except Exception:
        _slots.release()
        raise
    # Release only when the worker stops, even if the HTTP client disconnects.
    future.add_done_callback(lambda _: _slots.release())
    try:
        return await asyncio.wrap_future(future)
    except NoSpeechError as error:
        raise HTTPException(422, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(503, "Audio processing is unavailable. Check the speech engine and cached model setup.") from error
    except ValueError as error:
        raise HTTPException(422, "The recording format, duration, or audio contents are invalid.") from error
