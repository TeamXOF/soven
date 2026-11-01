"""Language inventory and runtime gates; a planned language is never a fallback."""
from copy import deepcopy
import json
from pathlib import Path
import re
from fastapi import HTTPException

_PATH = Path(__file__).resolve().parents[2] / 'shared/languages.json'
_CATALOG = json.loads(_PATH.read_text(encoding='utf-8'))
_LANGUAGES = {row['code']: row for row in _CATALOG['languages']}
_ALIASES = {'iw': 'he', 'in': 'id', 'ji': 'yi', 'tl': 'fil'}


def canonical_language(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*', value.strip()):
        raise ValueError('Invalid language identifier')
    base = value.strip().replace('_', '-').split('-')[0].lower()
    code = _ALIASES.get(base, base)
    if code not in _LANGUAGES:
        raise ValueError('Language is not in the SOVEN roadmap inventory')
    return code


def require_reading_language(value: str) -> str:
    try:
        code = canonical_language(value)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if not _LANGUAGES[code]['enabled_for_reading']:
        raise HTTPException(422, 'This language is planned but is not enabled for reading yet')
    return code


def language_catalog() -> dict:
    """Return an isolated public snapshot without runtime settings or secrets."""
    return deepcopy(_CATALOG)
