"""Tests for the edge-case / scaling guards."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.ingestion import ocr
from app.ingestion.indexer import _embed_batches
from app.main import app

client = TestClient(app)
AUTH = {"X-Password": settings.web_password}


# --- Embedding batches bounded by count and character budget ---

def test_embed_batches_split_on_char_budget():
    with patch.object(settings, "embed_batch_char_budget", 100):
        batches = _embed_batches(["a" * 60, "b" * 60, "c" * 60])
    assert [len(b) for b in batches] == [1, 1, 1]


def test_embed_batches_split_on_count():
    batches = _embed_batches(["x"] * 130)
    assert all(len(b) <= 64 for b in batches)
    assert sum(len(b) for b in batches) == 130


def test_embed_batches_preserve_order():
    texts = [f"t{i}" for i in range(10)]
    with patch.object(settings, "embed_batch_char_budget", 7):
        batches = _embed_batches(texts)
    assert [t for b in batches for t in b] == texts


# --- OCR file-size guard ---

def test_ocr_rejects_oversized_file(tmp_path: Path):
    big = tmp_path / "big.pdf"
    big.write_bytes(b"x" * 2_000_000)
    with patch.object(settings, "max_ocr_mb", 1):
        with pytest.raises(ValueError, match="above the OCR limit"):
            ocr.extract_pdf(big)


# --- Upload streaming cap ---

def test_upload_rejects_file_over_cap(tmp_path: Path):
    with patch.object(settings, "max_upload_mb", 1), \
         patch.object(settings, "uploads_dir", tmp_path):
        r = client.post("/api/upload", headers=AUTH,
                        files={"file": ("big.txt", b"y" * 2_000_000)},
                        data={"domain": "general"})
    assert r.status_code == 413
    assert not (tmp_path / "big.txt").exists()  # partial file cleaned up


# --- Chat rate limit ---

def test_chat_rate_limit_returns_429():
    from app import main as main_module
    from app.rag.chat import ChatAnswer

    fake = ChatAnswer(answer="ok", sources=[], log_ts="T")
    with patch.object(settings, "chat_rate_per_min", 2), \
         patch.object(main_module, "_chat_calls", []), \
         patch("app.main.rag_chat.ask", return_value=fake):
        codes = [
            client.post("/api/chat", headers=AUTH,
                        json={"question": "q", "domain": "all"}).status_code
            for _ in range(3)
        ]
    assert codes == [200, 200, 429]


# --- Long-audio segmentation decision ---

def test_long_audio_is_split(tmp_path: Path):
    from app.ingestion import audio

    f = tmp_path / "lecture.mp3"
    f.write_bytes(b"fake")
    with patch.object(audio, "duration_seconds", return_value=4 * 3600), \
         patch.object(audio, "_transcribe_segments", return_value="joined") as seg, \
         patch.object(audio, "_transcribe_one") as one:
        assert audio.transcribe_audio(f) == "joined"
    seg.assert_called_once()
    one.assert_not_called()


def test_short_audio_is_not_split(tmp_path: Path):
    from app.ingestion import audio

    f = tmp_path / "note.mp3"
    f.write_bytes(b"fake")
    with patch.object(audio, "duration_seconds", return_value=300), \
         patch.object(audio, "_transcribe_one", return_value="text") as one:
        assert audio.transcribe_audio(f) == "text"
    one.assert_called_once()
