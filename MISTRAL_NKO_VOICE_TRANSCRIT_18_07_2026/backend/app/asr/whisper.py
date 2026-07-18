"""Whisper engine (openai/whisper-large-v3 by default) — optional local engine.

Useful as a comparison/benchmark engine and for non-Manding languages when
running fully offline. Heavy dependencies are imported lazily.
"""

import io

from app.asr.base import ASREngine, EngineError, EngineUnavailable
from app.config import get_settings

_TARGET_SAMPLE_RATE = 16_000


class WhisperEngine(ASREngine):
    name = "whisper"

    def __init__(self):
        self._pipeline = None

    def _load(self):
        if self._pipeline is not None:
            return
        try:
            from transformers import pipeline
        except ImportError as error:
            raise EngineUnavailable(
                "Whisper engine requires: pip install torch torchaudio transformers"
            ) from error
        self._pipeline = pipeline(
            "automatic-speech-recognition", model=get_settings().whisper_model
        )

    def transcribe(self, audio: bytes, language: str) -> str:
        self._load()
        try:
            import torchaudio
        except ImportError as error:  # pragma: no cover - guarded in _load
            raise EngineUnavailable("torchaudio missing") from error
        try:
            waveform, rate = torchaudio.load(io.BytesIO(audio))
        except Exception as error:
            raise EngineError("Could not decode audio") from error
        waveform = waveform.mean(0)
        if rate != _TARGET_SAMPLE_RATE:
            waveform = torchaudio.functional.resample(waveform, rate, _TARGET_SAMPLE_RATE)
        result = self._pipeline(
            {"array": waveform.numpy(), "sampling_rate": _TARGET_SAMPLE_RATE}
        )
        return str(result.get("text", "")).strip()
