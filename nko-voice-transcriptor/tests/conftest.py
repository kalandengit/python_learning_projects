"""Shared fixtures: isolated app + database per test session."""

import os

import pytest

# Test configuration must exist before app modules import settings.
os.environ.setdefault("NKO_SECRET_KEY", "test-secret-key-0123456789abcdef-0123456789")
os.environ.setdefault("NKO_DATABASE_URL", "sqlite://")  # in-memory
os.environ.setdefault("NKO_ASR_ENGINE", "mock")
os.environ.setdefault("NKO_ENVIRONMENT", "development")

from fastapi.testclient import TestClient  # noqa: E402

from app.limits import limiter  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    limiter.enabled = False  # rate limits are covered by their own test
    with TestClient(app) as c:  # context manager runs lifespan (init_db etc.)
        yield c


@pytest.fixture()
def auth_headers(client):
    """A registered, logged-in user."""
    creds = {"username": "testuser", "password": "correct-horse9battery"}
    r = client.post("/api/auth/register", json=creds)
    assert r.status_code in (201, 409)  # 409 when reused across tests
    r = client.post("/api/auth/login", json=creds)
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
