"""Test fixtures: isolated SQLite database and authenticated clients."""

from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file before any app module is imported,
# and reset the cached settings so the value is picked up.
_TMP_DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["STAFFHUB_DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402

get_settings.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402

from app import deps  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    """Recreate the schema and clear rate limiters before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    for limiter in (
        deps.login_limiter,
        deps.upload_limiter,
        deps.request_limiter,
        deps.ics_limiter,
    ):
        limiter.reset()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tenant(client: TestClient) -> dict:
    resp = client.post("/auth/bootstrap-tenant", json={"name": "Acme", "slug": "acme"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _accept_and_login(client: TestClient, invite_token: str, email: str, password: str) -> str:
    r = client.post(
        "/auth/accept-invite", json={"token": invite_token, "password": password}
    )
    assert r.status_code == 200, r.text
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_token(client: TestClient, tenant: dict) -> str:
    r = client.post(
        f"/auth/tenants/{tenant['id']}/first-admin",
        json={"email": "admin@acme.io", "full_name": "Ada Admin"},
    )
    assert r.status_code == 201, r.text
    return _accept_and_login(client, r.json()["invite_token"], "admin@acme.io", "adminpass123")


def make_user(client: TestClient, tenant_id: str, admin_token: str, email: str, role: str) -> str:
    """Invite + activate a user, returning their access token."""
    r = client.post(
        f"/auth/tenants/{tenant_id}/invite",
        json={"email": email, "full_name": email.split("@")[0], "role": role},
        headers=_auth(admin_token),
    )
    assert r.status_code == 201, r.text
    return _accept_and_login(client, r.json()["invite_token"], email, "userpass123")


@pytest.fixture
def employee_token(client: TestClient, tenant: dict, admin_token: str) -> str:
    return make_user(client, tenant["id"], admin_token, "emp@acme.io", "employee")


@pytest.fixture
def planner_token(client: TestClient, tenant: dict, admin_token: str) -> str:
    return make_user(client, tenant["id"], admin_token, "planner@acme.io", "planner")


@pytest.fixture
def auth_header():
    return _auth
