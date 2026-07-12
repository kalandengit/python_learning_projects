"""Deterministic mock ASR engine.

Returns a Bambara phrase chosen by a stable hash of the audio content, so
the same upload always yields the same transcription. Lets the whole
pipeline, tests, and CI run with zero ML dependencies.
"""

from __future__ import annotations

import hashlib

from app.asr.base import ASREngine, ASRResult

_PHRASES: dict[str, tuple[str, ...]] = {
    "bam": (
        "i ni ce",                     # hello / thank you
        "n bɛ taa sugu la",            # I am going to the market
        "an ka bamanankan kalan",      # let's learn Bambara
        "aw ni sɔgɔma",                # good morning (to several people)
        "dɔɔnin dɔɔnin kɔnɔnin bɛ a ɲaga da",  # little by little the bird builds its nest
    ),
    "dyu": (
        "i ni sɔgɔma",                 # good morning
        "an bɛ julakan fɔ",            # we speak Dyula
        "i ka kɛnɛ wa",                # how are you
    ),
    "emk": (
        "i ni ke",                     # thank you
        "an ye maninkakan karan na",   # we are learning Maninka
        "tana ma si",                  # good morning (peaceful night?)
    ),
}
_FALLBACK = _PHRASES["bam"]


class MockASREngine(ASREngine):
    name = "mock"

    def transcribe(self, audio: bytes, audio_format: str, language: str = "bam") -> ASRResult:
        phrases = _PHRASES.get(language, _FALLBACK)
        digest = hashlib.sha256(audio).digest()
        phrase = phrases[digest[0] % len(phrases)]
        return ASRResult(text_latin=phrase, engine=self.name, language=language)
