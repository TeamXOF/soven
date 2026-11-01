"""Public provider inventory; metadata alone does not enable or invoke a model."""
from copy import deepcopy

_PROVIDERS = [
    {'id': 'google_reasoning', 'task': 'coaching', 'implementation': 'existing',
     'availability': 'configuration_dependent', 'language_quality': 'requires_per_language_validation'},
    {'id': 'groq_whisper', 'task': 'recognition', 'implementation': 'existing',
     'availability': 'configuration_dependent', 'word_timing': 'optional', 'confidence': 'optional'},
    {'id': 'local_whisper', 'task': 'recognition', 'implementation': 'existing',
     'availability': 'requires_installed_dependencies_and_cached_weights',
     'word_timing': 'word_or_explicitly_estimated', 'confidence': 'optional'},
    {'id': 'browser_speech_synthesis', 'task': 'speech_playback', 'implementation': 'existing',
     'availability': 'device_and_voice_dependent', 'offline_guaranteed': False},
    {'id': 'meta_reasoning', 'task': 'coaching', 'implementation': 'existing',
     'availability': 'requires_verified_permitted_access', 'adapter_implemented': True,
     'live_validation': 'not_performed'},
    {'id': 'chat_completions_reasoning', 'task': 'coaching', 'implementation': 'existing',
     'availability': 'requires_configured_verified_endpoint', 'adapter_implemented': True,
     'live_validation': 'not_performed'},
    {'id': 'meta_voice', 'task': 'recognition', 'implementation': 'planned',
     'availability': 'requires_verified_permitted_access', 'adapter_implemented': False,
     'word_timing': 'not_provided', 'confidence': 'not_provided',
     'reference': 'https://dev.meta.ai/docs/speech-to-text'},
]


def provider_inventory() -> list[dict]:
    return deepcopy(_PROVIDERS)
