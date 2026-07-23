"""Safe media normalization and silence-aware WAV segmentation."""

from __future__ import annotations

import io
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from app.asr.base import AudioValidationError


def _rms_pcm16(data: bytes) -> int:
    if len(data) < 2:
        return 0
    samples = memoryview(data[: len(data) - (len(data) % 2)]).cast("h")
    return int(math.sqrt(sum(value * value for value in samples) / len(samples)))


def normalize_media(data: bytes, source_format: str) -> bytes:
    """Convert supported audio/video to 16 kHz mono PCM WAV with FFmpeg."""
    if source_format == "wav":
        try:
            with wave.open(io.BytesIO(data), "rb") as src:
                is_normalized = (
                    src.getnchannels() == 1
                    and src.getframerate() == 16_000
                    and src.getsampwidth() == 2
                )
                if is_normalized:
                    return data
        except wave.Error:
            pass
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioValidationError("FFmpeg is required to process this media format")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"upload.{source_format}"
        target = Path(tmp) / "normalized.wav"
        source.write_bytes(data)
        command = [
            ffmpeg, "-nostdin", "-v", "error", "-y", "-i", str(source),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target),
        ]
        try:
            subprocess.run(command, check=True, timeout=120, capture_output=True)  # noqa: S603
        except (subprocess.SubprocessError, OSError) as exc:
            raise AudioValidationError("FFmpeg could not decode the uploaded media") from exc
        return target.read_bytes()


def segment_wav(data: bytes, max_seconds: int, silence_db: int) -> list[bytes]:
    """Split at quiet windows near the target length, dropping all-silent chunks."""
    try:
        with wave.open(io.BytesIO(data), "rb") as src:
            params = src.getparams()
            frames = src.readframes(src.getnframes())
    except wave.Error as exc:
        raise AudioValidationError("Normalized media is not a valid WAV") from exc
    rate, width = params.framerate, params.sampwidth
    frame_bytes = params.nchannels * width
    target = max_seconds * rate * frame_bytes
    window = max(1, rate // 5) * frame_bytes  # 200 ms
    threshold = int(32767 * (10 ** (silence_db / 20)))
    chunks: list[bytes] = []
    start = 0
    while start < len(frames):
        proposed = min(start + target, len(frames))
        end = proposed
        if proposed < len(frames):
            search_start = max(start + target // 2, proposed - 5 * rate * frame_bytes)
            quietest = min(
                range(search_start, proposed, window),
                key=lambda pos: _rms_pcm16(frames[pos : pos + window]),
                default=proposed,
            )
            if _rms_pcm16(frames[quietest : quietest + window]) <= threshold:
                end = quietest + window
        payload = frames[start:end]
        if payload and _rms_pcm16(payload) > max(1, threshold // 4):
            output = io.BytesIO()
            with wave.open(output, "wb") as dst:
                dst.setparams(params)
                dst.writeframes(payload)
            chunks.append(output.getvalue())
        start = max(end, start + frame_bytes)
    return chunks or [data]
