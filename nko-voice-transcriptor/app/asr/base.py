"""ASR engine interface, audio validation, and engine factory.

Engines take raw uploaded audio bytes and return Bambara text in Latin
orthography; the N'Ko conversion happens downstream in ``app.nko``.

Two engines ship:

* ``mock`` — deterministic, dependency-free; used for tests, CI, and demo
  environments without the ~2 GB torch/transformers stack.
* ``mms`` — Meta's Massively Multilingual Speech model with the Bambara
  (``bam``) adapter; the real engine for production. Loaded lazily on first
  use so the app starts fast and works without ML deps installed.
"""

from __future__ import annotations

import abc
import struct
from dataclasses import dataclass

from app.config import Settings

# Magic-byte signatures for the container formats browsers actually produce.
_SIGNATURES: dict[str, tuple[bytes, int]] = {
    # format: (magic, offset)
    "wav": (b"RIFF", 0),
    "ogg": (b"OggS", 0),
    "webm": (b"\x1a\x45\xdf\xa3", 0),  # EBML (webm/mkv)
    "mp3-id3": (b"ID3", 0),
    "mp4": (b"ftyp", 4),
}

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/ogg",
        "audio/webm",
        "video/webm",  # Chrome MediaRecorder labels audio-only webm this way
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
    }
)


class AudioValidationError(ValueError):
    """Uploaded audio failed validation (type, size, or content)."""


@dataclass(frozen=True)
class ASRResult:
    text_latin: str
    engine: str
    language: str = "bam"


def sniff_format(data: bytes) -> str | None:
    """Identify the audio container from magic bytes; None if unknown."""
    if len(data) >= 3 and data[:2] == b"\xff" and (data[2] & 0xE0) == 0xE0:
        return "mp3"  # raw MPEG frame sync
    for fmt, (magic, offset) in _SIGNATURES.items():
        if data[offset : offset + len(magic)] == magic:
            return fmt.split("-")[0]
    return None


def validate_audio(data: bytes, content_type: str | None, settings: Settings) -> str:
    """Validate uploaded audio; returns the sniffed format.

    Defense in depth: we check the declared content type AND the actual
    magic bytes — a client-supplied MIME type is never trusted alone.
    """
    if not data:
        raise AudioValidationError("Empty audio upload")
    if len(data) > settings.max_upload_bytes:
        raise AudioValidationError(
            f"Audio exceeds the {settings.max_upload_bytes // (1024 * 1024)} MiB limit"
        )
    if content_type and content_type.split(";")[0].strip() not in ALLOWED_CONTENT_TYPES:
        raise AudioValidationError(f"Unsupported content type: {content_type}")
    fmt = sniff_format(data)
    if fmt is None:
        raise AudioValidationError("File does not look like a supported audio format")
    return fmt


def wav_duration_seconds(data: bytes) -> float | None:
    """Duration of a PCM WAV payload, or None if not parseable as WAV."""
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return None
    # Walk RIFF chunks to find fmt + data sizes.
    byte_rate = None
    data_size = None
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        (chunk_size,) = struct.unpack("<I", data[pos + 4 : pos + 8])
        if chunk_id == b"fmt " and pos + 16 <= len(data):
            byte_rate = struct.unpack("<I", data[pos + 16 : pos + 20])[0]
        elif chunk_id == b"data":
            data_size = chunk_size
        pos += 8 + chunk_size + (chunk_size % 2)
    if byte_rate and data_size:
        return data_size / byte_rate
    return None


class ASREngine(abc.ABC):
    """Speech-to-text engine contract."""

    name: str = "abstract"

    @abc.abstractmethod
    def transcribe(self, audio: bytes, audio_format: str, language: str = "bam") -> ASRResult:
        """Transcribe audio bytes to Manding Latin text in the given language."""


def get_engine(settings: Settings) -> ASREngine:
    """Engine factory driven by ``NKO_ASR_ENGINE``."""
    if settings.asr_engine == "mms":
        from app.asr.mms import MMSASREngine

        return MMSASREngine(settings)
    from app.asr.mock import MockASREngine

    return MockASREngine()
