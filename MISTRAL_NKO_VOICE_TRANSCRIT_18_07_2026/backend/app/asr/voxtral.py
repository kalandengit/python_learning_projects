"""Mistral Voxtral Transcribe engine (server-side API calls only).

The API key lives exclusively in server configuration; clients never see
it. Requests carry only the audio and language — no user identifiers.
"""

import logging

import httpx

from app.asr.base import ASREngine, EngineError, EngineUnavailable
from app.config import get_settings

logger = logging.getLogger("nko.asr.voxtral")

_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=60.0, pool=10.0)


class VoxtralEngine(ASREngine):
    name = "voxtral"

    def transcribe(self, audio: bytes, language: str) -> str:
        settings = get_settings()
        if settings.mistral_api_key is None:
            raise EngineUnavailable("Mistral API key not configured")
        url = f"{settings.mistral_api_base}/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {settings.mistral_api_key.get_secret_value()}"}
        data = {"model": settings.mistral_transcribe_model, "language": language}
        files = {"file": ("audio", audio)}
        try:
            response = httpx.post(
                url, headers=headers, data=data, files=files, timeout=_TIMEOUT
            )
        except httpx.HTTPError as error:
            raise EngineError("Mistral API unreachable") from error
        if response.status_code != 200:
            logger.warning("voxtral_error status=%s", response.status_code)
            raise EngineError(f"Mistral API returned {response.status_code}")
        payload = response.json()
        text = payload.get("text")
        if not isinstance(text, str):
            raise EngineError("Malformed Mistral API response")
        return text.strip()
