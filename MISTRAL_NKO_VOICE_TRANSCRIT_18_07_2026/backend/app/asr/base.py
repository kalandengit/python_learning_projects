"""ASR engine interface."""

import abc


class EngineError(RuntimeError):
    """Transcription failed inside an engine (maps to 502)."""


class EngineUnavailable(RuntimeError):
    """Engine not configured/installed (maps to 503)."""


class ASREngine(abc.ABC):
    name: str

    @abc.abstractmethod
    def transcribe(self, audio: bytes, language: str) -> str:
        """Return Latin-orthography text for the given audio bytes."""


# ISO 639-3 codes for the Manding continuum handled by the local engine.
MANDING_LANGUAGES = frozenset({"bam", "dyu", "emk", "man", "mnk", "jul"})

# Languages Voxtral Transcribe supports natively (July 2026).
VOXTRAL_LANGUAGES = frozenset(
    {"en", "fr", "es", "de", "it", "pt", "nl", "hi", "zh", "ar", "ru", "ja", "ko"}
)
