"""Auth integration: refresh rotation + reuse detection, lockout, enumeration, MFA."""

from __future__ import annotations

import uuid

import httpx
import pyotp
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from tests.conftest import TEST_PASSWORD, MakeUser

pytestmark = pytest.mark.db


def _email() -> str:
    return f"auth-{uuid.uuid4().hex[:12]}@test.ems"


async def _register(client: httpx.AsyncClient, email: str, **extra: object) -> httpx.Response:
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": TEST_PASSWORD, **extra},
    )


async def test_register_and_login(client: httpx.AsyncClient, db_session: AsyncSession) -> None:
    email = _email()
    r = await _register(client, email, organization_name=f"org-{uuid.uuid4().hex[:8]}")
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"] and body["refresh_token"]

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None and user.role is UserRole.EVENT_ORGANIZER
    assert user.password_hash is not None and user.password_hash.startswith("$argon2id$")

    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD}
    )
    assert r.status_code == 200 and r.json()["access_token"]


async def test_register_without_org_is_attendee(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    email = _email()
    assert (await _register(client, email)).status_code == 201
    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None and user.role is UserRole.ATTENDEE


async def test_refresh_rotation_and_reuse_detection(client: httpx.AsyncClient) -> None:
    email = _email()
    original = (await _register(client, email)).json()

    # Rotate once — new pair comes back.
    r1 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )
    assert r1.status_code == 200
    rotated = r1.json()
    assert rotated["refresh_token"] != original["refresh_token"]

    # Reusing the OLD token is a theft signal → 401 and the family is revoked.
    r2 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )
    assert r2.status_code == 401

    # The rotated token dies with its family.
    r3 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}
    )
    assert r3.status_code == 401


async def test_logout_revokes_family(client: httpx.AsyncClient) -> None:
    tokens = (await _register(client, _email())).json()
    assert (
        await client.post(
            "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
    ).status_code == 204
    r = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 401


async def test_lockout_after_five_failures(client: httpx.AsyncClient) -> None:
    email = _email()
    await _register(client, email)
    for _ in range(5):
        r = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong-password-x"}
        )
        assert r.status_code == 401
    # Locked now — even the CORRECT password is refused for 15 minutes.
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert r.status_code == 429


async def test_no_account_enumeration_on_login(client: httpx.AsyncClient) -> None:
    email = _email()
    await _register(client, email)
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": f"ghost-{uuid.uuid4().hex[:8]}@test.ems", "password": "whatever-long"},
    )
    wrong_pw = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password-x"}
    )
    # Identical status AND identical body — nothing distinguishes the cases.
    assert unknown.status_code == wrong_pw.status_code == 401
    assert unknown.json() == wrong_pw.json()


async def test_no_enumeration_on_duplicate_register(client: httpx.AsyncClient) -> None:
    email = _email()
    await _register(client, email)
    dup = await _register(client, email)
    assert dup.status_code == 400
    assert email not in dup.text  # generic message, no echo of the address


async def test_mfa_setup_verify_and_login(client: httpx.AsyncClient) -> None:
    email = _email()
    tokens = (await _register(client, email)).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert r.status_code == 200
    secret = r.json()["secret"]

    # Arm MFA by confirming a code while authenticated.
    code = pyotp.TOTP(secret).now()
    r = await client.post("/api/v1/auth/mfa/verify", json={"code": code}, headers=headers)
    assert r.status_code == 200

    # Login now requires the second factor.
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body.get("mfa_required") is True

    r = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": pyotp.TOTP(secret).now(), "mfa_token": body["mfa_token"]},
    )
    assert r.status_code == 200 and r.json()["access_token"]

    # Wrong code → generic 401.
    r = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": "000000", "mfa_token": body["mfa_token"]},
    )
    assert r.status_code == 401


async def test_legacy_bcrypt_rehashed_on_login(
    client: httpx.AsyncClient, db_session: AsyncSession, make_user: MakeUser
) -> None:
    import bcrypt as _bcrypt

    user, _ = await make_user()
    user.password_hash = _bcrypt.hashpw(TEST_PASSWORD.encode(), _bcrypt.gensalt(rounds=4)).decode()
    await db_session.commit()

    r = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": TEST_PASSWORD}
    )
    assert r.status_code == 200
    await db_session.refresh(user)
    assert user.password_hash is not None and user.password_hash.startswith("$argon2id$")


async def test_protected_endpoint_requires_token(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/tickets/mine")).status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await client.get("/api/v1/tickets/mine", headers=bad)).status_code == 401


async def test_passkey_options_endpoints(client: httpx.AsyncClient, app: FastAPI) -> None:
    tokens = (await _register(client, _email())).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = await client.post("/api/v1/auth/passkeys/register/options", headers=headers)
    assert r.status_code == 200
    opts = r.json()
    assert opts["authenticatorSelection"]["userVerification"] == "required"
    assert opts["authenticatorSelection"]["residentKey"] == "required"

    r = await client.post("/api/v1/auth/passkeys/login/options")
    assert r.status_code == 200
    assert r.json()["challenge_id"]

    # Verify without a stored challenge / with garbage → generic 401.
    r = await client.post(
        "/api/v1/auth/passkeys/login/verify",
        json={"challenge_id": "deadbeef", "credential": {"rawId": "AAAA"}},
    )
    assert r.status_code == 401
