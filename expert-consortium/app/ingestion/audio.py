"""Audio and video transcription: Voxtral for speech, ffmpeg to pull audio from video.

Long recordings (over settings.audio_segment_minutes) are split into segments with
ffmpeg, transcribed one by one, and merged — so a 5-hour lecture ingests fine even
though the API caps a single transcription request.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.config import settings, setup_logging
from app.mistral_client import get_client, with_retry

logger = setup_logging()

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".opus"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}

_FFMPEG_TIMEOUT = 3600  # seconds; re-encoding hours of media is slow but bounded


def _run_ffmpeg(args: list[str], context: str) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", *args], capture_output=True, text=True, timeout=_FFMPEG_TIMEOUT
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed while {context} (is ffmpeg installed? see "
            f"docs/en/01-setup.md step 3): {result.stderr[-500:]}"
        )


def duration_seconds(path: Path) -> float | None:
    """Media duration via ffprobe; None when it can't be determined."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return None


def _transcribe_one(path: Path) -> str:
    resp = with_retry(
        get_client().audio.transcriptions.complete,
        model=settings.transcribe_model,
        file={"content": path.read_bytes(), "file_name": path.name},
    )
    return resp.text


def _transcribe_segments(path: Path, segment_seconds: int) -> str:
    """Split a long recording into segments, transcribe each, merge the texts."""
    with tempfile.TemporaryDirectory() as tmp:
        pattern = Path(tmp) / "segment-%03d.mp3"
        _run_ffmpeg(
            ["-i", str(path), "-f", "segment", "-segment_time", str(segment_seconds),
             "-vn", "-acodec", "libmp3lame", "-b:a", "64k", str(pattern)],
            f"splitting {path.name}",
        )
        segments = sorted(Path(tmp).glob("segment-*.mp3"))
        logger.info("Transcribing %s in %d segments", path.name, len(segments))
        parts = []
        for i, segment in enumerate(segments, 1):
            logger.info("  segment %d/%d", i, len(segments))
            parts.append(_transcribe_one(segment))
        return "\n\n".join(parts)


def transcribe_audio(path: Path) -> str:
    limit_seconds = settings.audio_segment_minutes * 60
    duration = duration_seconds(path)
    if duration is not None and duration > limit_seconds:
        return _transcribe_segments(path, limit_seconds)
    return _transcribe_one(path)


def extract_video(path: Path) -> str:
    """Extract the audio track with ffmpeg, then transcribe it (splitting if long)."""
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / (path.stem + ".mp3")
        _run_ffmpeg(
            ["-i", str(path), "-vn", "-acodec", "libmp3lame", "-b:a", "64k",
             str(audio_path)],
            f"extracting audio from {path.name}",
        )
        return transcribe_audio(audio_path)
