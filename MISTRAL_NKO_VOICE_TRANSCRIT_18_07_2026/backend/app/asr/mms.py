"""Local MMS engine (facebook/mms-1b-all) with pinned revision.

Torch/torchaudio/transformers are optional heavy dependencies; they are
imported lazily so the rest of the app (and CI) runs without them.
The model revision is pinned via ``NKO_MMS_REVISION`` and downloads can be
disabled entirely with ``NKO_MMS_LOCAL_FILES_ONLY`` (supply-chain finding).
"""

import io
import logging

from app.asr.base import ASREngine, EngineError, EngineUnavailable
from app.config import get_settings

logger = logging.getLogger("nko.asr.mms")

_TARGET_SAMPLE_RATE = 16_000


class MMSEngine(ASREngine):
    name = "mms"

    def __init__(self):
        self._processor = None
        self._model = None
        self._loaded_language: str | None = None

    def _load(self, language: str):
        try:
            import torch  # noqa: F401
            from transformers import AutoProcessor, Wav2Vec2ForCTC
        except ImportError as error:
            raise EngineUnavailable(
                "MMS engine requires the ASR extra: pip install torch torchaudio transformers"
            ) from error
        settings = get_settings()
        source = settings.mms_model_dir or settings.mms_model_id
        kwargs = {
            "revision": settings.mms_revision,
            "local_files_only": settings.mms_local_files_only or bool(settings.mms_model_dir),
        }
        if self._processor is None:
            logger.info("loading_mms model=%s revision=%s", source, settings.mms_revision)
            # Revision IS pinned — passed via kwargs["revision"] above.
            self._processor = AutoProcessor.from_pretrained(source, **kwargs)  # nosec B615
            self._model = Wav2Vec2ForCTC.from_pretrained(source, **kwargs)  # nosec B615
        if self._loaded_language != language:
            self._processor.tokenizer.set_target_lang(language)
            self._model.load_adapter(language)
            self._loaded_language = language

    def transcribe(self, audio: bytes, language: str) -> str:
        self._load(language)
        try:
            import torch
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
        inputs = self._processor(
            waveform.numpy(), sampling_rate=_TARGET_SAMPLE_RATE, return_tensors="pt"
        )
        with torch.inference_mode():
            logits = self._model(**inputs).logits
        return self._processor.batch_decode(logits.argmax(-1))[0].strip()
