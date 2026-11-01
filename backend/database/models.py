from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from core.language_types import ReadingLanguage

class StudentCreate(BaseModel):
    name: str
    grade: int

class PipelineRunRequest(BaseModel):
    student_id: str
    target_sentence: str = Field(min_length=1, max_length=2000)
    audio_base64: Optional[str] = None
    language: ReadingLanguage = "en"
    # For demo without real audio, we accept mocked signal data
    mocked_signal_data: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
