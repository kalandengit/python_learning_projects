"""Test fixtures: isolated settings, SQLite database, HTTP client."""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="nko-tests-")
os.environ["NKO_SECRET_KEY"] = "test-secret-key-0123456789abcdef-0123456789"
os.environ["NKO_DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["NKO_ASR_ENGINE"] = "mock"
os.environ["NKO_RATE_LIMIT_AUTH"] = "1000/minute"
os.environ["NKO_RATE_LIMIT_TRANSCRIBE"] = "1000/minute"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, get_engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(get_engine())


@pytest.fixture
def client():
    return TestClient(app)


def make_wav(payload: bytes = b"\x00\x01" * 400) -> bytes:
    """Minimal but magic-byte-valid RIFF/WAVE blob."""
    body = b"WAVEfmt " + b"\x10\x00\x00\x00" + b"\x00" * 16 + b"data" + payload
    return b"RIFF" + len(body).to_bytes(4, "little") + body


@pytest.fixture
def wav_bytes():
    return make_wav()


_COUNTER = {"n": 0}


@pytest.fixture
def user_factory(client):
    def _create(password: str = "correct-horse-battery"):
        _COUNTER["n"] += 1
        email = f"user{_COUNTER['n']}@example.com"
        response = client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        assert response.status_code == 201, response.text
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert login.status_code == 200, login.text
        return email, login.json()

    return _create
