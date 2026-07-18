"""Deterministic mock engine for development, CI, and tests."""

import hashlib

from app.asr.base import ASREngine

_SAMPLES = {
    "bam": "i ni ce",
    "dyu": "i ni sɔgɔma",
    "emk": "i ni ke",
    "fr": "bonjour tout le monde",
    "en": "hello everyone",
}


class MockEngine(ASREngine):
    name = "mock"

    def transcribe(self, audio: bytes, language: str) -> str:
        base = _SAMPLES.get(language, "i ni ce")
        # Stable per-input suffix so tests can distinguish different uploads.
        digest = hashlib.sha256(audio).hexdigest()[:6]
        return f"{base} [{digest}]"
