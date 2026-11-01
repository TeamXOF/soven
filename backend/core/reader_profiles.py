"""Account preferences, separate from learner records and historical attempts."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from core.language_types import LanguageCode, ReadingLanguage


class AccessibilitySettings(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    larger_text: bool = False
    word_tips: bool = True
    high_contrast: bool = False
    line_spacing: Literal['normal', 'comfortable', 'wide'] = 'normal'
    coach_enabled: bool = True
    autoplay_coach: bool = False


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_version: int = Field(ge=1)
    reading_language: ReadingLanguage | None = None
    interface_language: ReadingLanguage | None = None
    native_language: LanguageCode | None = None
    translation_language: LanguageCode | None = None
    accessibility: AccessibilitySettings | None = None
    complete_profile: bool = False


def create_profile(conn, user_id: str, mode: str, completed: bool = False):
    conn.execute('''INSERT OR IGNORE INTO user_profiles
        (user_id, reader_mode, profile_completed) VALUES (?, ?, ?)''',
        (user_id, mode, int(completed)))


def read_profile(conn, user: dict) -> dict:
    row = conn.execute('SELECT * FROM user_profiles WHERE user_id=?', (user['id'],)).fetchone()
    # Old integrations can create users directly. Missing rows retain legacy access.
    data = dict(row) if row else {
        'user_id': user['id'], 'reader_mode': 'teacher' if user['role'] == 'teacher' else 'child',
        'reading_language': 'en', 'interface_language': 'en', 'native_language': None,
        'translation_language': None, 'accessibility_json': '{}', 'profile_completed': 1,
        'version': 1, 'updated_at': None,
    }
    try:
        accessibility = AccessibilitySettings.model_validate(json.loads(data.pop('accessibility_json')))
    except (ValueError, TypeError, ValidationError):
        accessibility = AccessibilitySettings()
    data['accessibility'] = accessibility.model_dump()
    data['profile_completed'] = bool(data['profile_completed'])
    return data
