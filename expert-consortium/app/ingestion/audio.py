"""Audio and video transcription: Voxtral for speech, ffmpeg to pull audio from video."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.config import settings
from app.mistral_client import get_client, with_retry

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".opus"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


def transcribe_audio(path: Path) -> str:
    resp = with_retry(
        get_client().audio.transcriptions.complete,
        model=settings.transcribe_model,
        file={"content": path.read_bytes(), "file_name": path.name},
    )
    return resp.text


def extract_video(path: Path) -> str:
    """Extract the audio track with ffmpeg, then transcribe it."""
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / (path.stem + ".mp3")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(path), "-vn", "-acodec", "libmp3lame",
             "-b:a", "64k", str(audio_path)],
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed on {path.name} (is ffmpeg installed? see docs/en/01-setup.md "
                f"step 3): {result.stderr[-500:]}"
            )
        return transcribe_audio(audio_path)
