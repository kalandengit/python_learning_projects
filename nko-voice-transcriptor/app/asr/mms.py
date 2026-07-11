"""Meta MMS speech recognition engine (Bambara adapter).

Requires the optional heavy dependencies::

    pip install torch torchaudio transformers

The model (``facebook/mms-1b-all`` by default, ~4 GB with weights) is
downloaded on first use and cached by huggingface_hub. Loading is lazy and
thread-safe so app startup stays fast and the ``mock`` engine keeps working
where torch is not installed.
"""

from __future__ import annotations

import io
import threading

from app.asr.base import ASREngine, ASRResult, AudioValidationError
from app.config import Settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

_TARGET_SAMPLE_RATE = 16_000


class MMSASREngine(ASREngine):
    name = "mms"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._model = None
        self._processor = None

    def _load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            try:
                from transformers import AutoProcessor, Wav2Vec2ForCTC
            except ImportError as exc:  # pragma: no cover - env without torch
                raise RuntimeError(
                    "MMS engine requires optional deps: pip install torch torchaudio transformers"
                ) from exc
            logger.info(
                "event=mms_load_start model=%s lang=%s",
                self._settings.mms_model_id,
                self._settings.mms_target_lang,
            )
            processor = AutoProcessor.from_pretrained(
                self._settings.mms_model_id, target_lang=self._settings.mms_target_lang
            )
            model = Wav2Vec2ForCTC.from_pretrained(
                self._settings.mms_model_id,
                target_lang=self._settings.mms_target_lang,
                ignore_mismatched_sizes=True,
            )
            model.eval()
            self._processor, self._model = processor, model
            logger.info("event=mms_load_done")

    def _decode_audio(self, audio: bytes):
        """Decode container bytes to a 16 kHz mono float tensor."""
        import torch
        import torchaudio

        try:
            waveform, sample_rate = torchaudio.load(io.BytesIO(audio))
        except Exception as exc:
            raise AudioValidationError(f"Could not decode audio: {exc}") from exc
        if waveform.shape[0] > 1:  # downmix to mono
            waveform = waveform.mean(dim=0, keepdim=True)
        if sample_rate != _TARGET_SAMPLE_RATE:
            waveform = torchaudio.functional.resample(
                waveform, sample_rate, _TARGET_SAMPLE_RATE
            )
        duration = waveform.shape[1] / _TARGET_SAMPLE_RATE
        if duration > self._settings.max_audio_seconds:
            raise AudioValidationError(
                f"Audio longer than {self._settings.max_audio_seconds}s limit"
            )
        return waveform.squeeze(0).to(torch.float32)

    def transcribe(self, audio: bytes, audio_format: str) -> ASRResult:
        self._load()
        import torch

        waveform = self._decode_audio(audio)
        inputs = self._processor(
            waveform.numpy(), sampling_rate=_TARGET_SAMPLE_RATE, return_tensors="pt"
        )
        with torch.no_grad():
            logits = self._model(**inputs).logits
        ids = torch.argmax(logits, dim=-1)[0]
        text = self._processor.decode(ids)
        return ASRResult(text_latin=text.strip(), engine=self.name)
