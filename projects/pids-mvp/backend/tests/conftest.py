"""Pytest fixtures — isolate each test run in a throwaway SQLite database."""
from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a temp DB BEFORE importing anything that reads settings.
_TMP_DB = os.path.join(tempfile.mkdtemp(), "test_pids.db")
os.environ["PIDS_DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["PIDS_SECRET_KEY"] = "test-secret"
os.environ["PIDS_DEDUP_WINDOW_SECONDS"] = "30"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:  # runs lifespan (init_db + seed)
        yield c


@pytest.fixture()
def admin_token(client):
    from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD

    resp = client.post(
        "/api/v1/auth/token",
        data={"username": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
