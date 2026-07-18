"""Language → engine routing.

- Manding languages go to the local engine (``mock`` in dev, ``mms`` in
  production) because Voxtral does not support them.
- Voxtral-supported languages use the Mistral API when a key is configured.
- An explicit engine override is honored after validation.
"""

from functools import lru_cache

from app.asr.base import (
    MANDING_LANGUAGES,
    VOXTRAL_LANGUAGES,
    ASREngine,
    EngineUnavailable,
)
from app.asr.mms import MMSEngine
from app.asr.mock import MockEngine
from app.asr.voxtral import VoxtralEngine
from app.asr.whisper import WhisperEngine
from app.config import get_settings


@lru_cache
def _engines() -> dict[str, ASREngine]:
    return {
        "mock": MockEngine(),
        "mms": MMSEngine(),
        "whisper": WhisperEngine(),
        "voxtral": VoxtralEngine(),
    }


def route_language(language: str) -> str:
    settings = get_settings()
    if language in MANDING_LANGUAGES:
        return settings.asr_engine
    if language in VOXTRAL_LANGUAGES and settings.mistral_api_key is not None:
        return "voxtral"
    # MMS covers 1,100+ languages; fall back to the configured local engine.
    return settings.asr_engine


def get_engine(language: str, override: str | None = None) -> ASREngine:
    name = override or route_language(language)
    engines = _engines()
    if name not in engines:
        raise EngineUnavailable(f"Unknown engine '{name}'")
    return engines[name]
