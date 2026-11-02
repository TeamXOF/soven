"""Read-only public capabilities for future onboarding; no inference or user data."""
from fastapi import APIRouter
from core.languages import language_catalog
from core.provider_capabilities import provider_inventory
from core.speech_capabilities import language_speech_inventory

router = APIRouter(prefix='/api/v1', tags=['capabilities'])


@router.get('/capabilities')
def capabilities():
    return {'schema_version': 1, 'language_catalog': language_catalog(),
            'providers': provider_inventory(), 'language_speech': language_speech_inventory(),
            'notice': 'Catalogued languages are planned unless explicitly enabled. Metadata does not establish provider availability or assessment validity.'}
