"""Report runtime prerequisites without sending audio or making provider calls."""
import importlib.util
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import settings

missing=[]
for module in ['fastapi','uvicorn','requests','librosa','faster_whisper','multipart','dotenv']:
    present=importlib.util.find_spec(module) is not None
    print(f'{module}: {"installed" if present else "missing"}')
    if not present: missing.append(module)
ffmpeg=bool(shutil.which('ffmpeg') or (Path(__file__).resolve().parents[1]/'ffmpeg.exe').exists())
print(f'ffmpeg: {"available" if ffmpeg else "missing"}')
print(f'Local speech model requested: {settings.WHISPER_MODEL}')
print('Model weights must be cached and tested before going offline; this check does not load or download them.')
raise SystemExit(1 if missing or not ffmpeg else 0)
