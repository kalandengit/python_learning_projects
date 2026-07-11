"""Deterministic mock ASR engine.

Returns a Bambara phrase chosen by a stable hash of the audio content, so
the same upload always yields the same transcription. Lets the whole
pipeline, tests, and CI run with zero ML dependencies.
"""

from __future__ import annotations

import hashlib

from app.asr.base import ASREngine, ASRResult

_PHRASES = (
    "i ni ce",                     # hello / thank you
    "n bɛ taa sugu la",            # I am going to the market
    "an ka bamanankan kalan",      # let's learn Bambara
    "aw ni sɔgɔma",                # good morning (to several people)
    "dɔɔnin dɔɔnin kɔnɔnin bɛ a ɲaga da",  # little by little the bird builds its nest
)


class MockASREngine(ASREngine):
    name = "mock"

    def transcribe(self, audio: bytes, audio_format: str) -> ASRResult:
        digest = hashlib.sha256(audio).digest()
        phrase = _PHRASES[digest[0] % len(_PHRASES)]
        return ASRResult(text_latin=phrase, engine=self.name)
