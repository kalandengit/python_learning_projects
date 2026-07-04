"""Test fixtures: real PostgreSQL (PostGIS) + Valkey-protocol server.

Environment (override in CI):
    EMS_DATABASE_URL  postgresql+asyncpg://ems@127.0.0.1:55432/ems_test
    EMS_VALKEY_URL    redis://127.0.0.1:56379/0

The schema is built by running the real Alembic migrations once per session;
tables are truncated between tests (TRUNCATE bypasses the append-only row
triggers on the audit tables, so cleanup still works).
"""

from __future__ import annotations

import asyncio
import os
import secrets
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

os.environ.setdefault("EMS_ENV", "test")
os.environ.setdefault(
    "EMS_DATABASE_URL", "postgresql+asyncpg://ems@127.0.0.1:55432/ems_test"
)
os.environ.setdefault("EMS_VALKEY_URL", "redis://127.0.0.1:56379/0")
os.environ.setdefault("EMS_PQC_ALLOW_HMAC_ONLY", "true")
os.environ.setdefault("EMS_STRIPE_WEBHOOK_SECRET", "whsec_test_secret")

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.core.security import AuthContext, hash_password
from app.models import Event, Organization, TicketTier, User, UserRole

REPO_ROOT = Path(__file__).resolve().parent.parent

_TABLES = (
    "scan_logs",
    "ticket_status_history",
    "tickets",
    "payments",
    "badges",
    "ticket_tiers",
    "events",
    "webauthn_credentials",
    "users",
    "organizations",
)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """Reset the schema and run `alembic upgrade head` against the test DB."""
    url = os.environ["EMS_DATABASE_URL"]

    async def _reset() -> None:
        engine = create_async_engine(url, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await engine.dispose()

    asyncio.run(_reset())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=REPO_ROOT,
        env=os.environ.copy(),
    )


@pytest.fixture(scope="session")
async def app(apply_migrations: None) -> AsyncIterator[FastAPI]:
    from app.main import create_app

    application = create_app(Settings())
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture(autouse=True)
async def _clean_state(app: FastAPI) -> AsyncIterator[None]:
    yield
    async with app.state.engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE")
        )
    await app.state.valkey.flushdb()


@pytest.fixture()
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture()
async def db_session(app: FastAPI) -> AsyncIterator[AsyncSession]:
    async with app.state.sessionmaker() as session:
        yield session


TEST_PASSWORD = "correct-horse-battery-staple-9!"

MakeUser = Callable[..., Awaitable[tuple[User, dict[str, str]]]]
MakeEvent = Callable[..., Awaitable[tuple[Event, TicketTier]]]


@pytest.fixture()
def make_user(app: FastAPI, db_session: AsyncSession) -> MakeUser:
    async def _make(
        role: UserRole = UserRole.ATTENDEE,
        *,
        email: str | None = None,
        password: str = TEST_PASSWORD,
        organization: Organization | None = None,
    ) -> tuple[User, dict[str, str]]:
        org = organization or Organization(name=f"org-{uuid.uuid4().hex[:12]}")
        user = User(
            organization=org,
            email=email or f"user-{uuid.uuid4().hex[:12]}@test.ems",
            password_hash=hash_password(password),
            role=role,
        )
        db_session.add(user)
        await db_session.commit()
        token = app.state.token_issuer.issue_access(user.id, user.organization_id, role)
        return user, {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture()
def make_event(db_session: AsyncSession) -> MakeEvent:
    async def _make(
        organization_id: uuid.UUID,
        *,
        price_cents: int = 0,
        capacity: int = 50,
        published: bool = True,
    ) -> tuple[Event, TicketTier]:
        now = datetime.now(UTC)
        event = Event(
            organization_id=organization_id,
            title=f"Event {uuid.uuid4().hex[:8]}",
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=4),
            is_published=published,
        )
        tier = TicketTier(
            event=event,
            name="General",
            price_cents=price_cents,
            currency="eur",
            capacity=capacity,
        )
        db_session.add_all([event, tier])
        await db_session.commit()
        return event, tier

    return _make


def auth_ctx(user: User) -> AuthContext:
    return AuthContext(user_id=user.id, org_id=user.organization_id, role=user.role)


def idem() -> str:
    return secrets.token_hex(16)
