"""Events (cursor pagination, IDOR on drafts) and GDPR endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from tests.conftest import TEST_PASSWORD, MakeEvent, MakeUser, idem

pytestmark = pytest.mark.db


async def test_event_create_publish_and_detail(
    client: httpx.AsyncClient, make_user: MakeUser
) -> None:
    _, headers = await make_user(UserRole.EVENT_ORGANIZER)
    now = datetime.now(UTC)
    r = await client.post(
        "/api/v1/events",
        json={
            "title": "PQC Summit",
            "starts_at": (now + timedelta(days=7)).isoformat(),
            "ends_at": (now + timedelta(days=7, hours=8)).isoformat(),
            "venue_name": "Paris Expo",
            "latitude": 48.8322,
            "longitude": 2.2875,
            "geofence_radius_m": 250,
        },
        headers=headers,
    )
    assert r.status_code == 201
    event = r.json()
    assert event["is_published"] is False
    assert abs(event["latitude"] - 48.8322) < 1e-6
    assert abs(event["longitude"] - 2.2875) < 1e-6

    # Draft: invisible to the public and to other orgs (404, not 403).
    assert (await client.get(f"/api/v1/events/{event['id']}")).status_code == 404
    _, other = await make_user(UserRole.EVENT_ORGANIZER)
    assert (
        await client.get(f"/api/v1/events/{event['id']}", headers=other)
    ).status_code == 404
    # Visible to its own org.
    assert (
        await client.get(f"/api/v1/events/{event['id']}", headers=headers)
    ).status_code == 200

    r = await client.post(f"/api/v1/events/{event['id']}/publish", headers=headers)
    assert r.status_code == 200 and r.json()["is_published"] is True
    assert (await client.get(f"/api/v1/events/{event['id']}")).status_code == 200

    # Tier creation is org-scoped too.
    tier = {"name": "GA", "price_cents": 0, "capacity": 100}
    assert (
        await client.post(f"/api/v1/events/{event['id']}/tiers", json=tier, headers=other)
    ).status_code == 404
    assert (
        await client.post(f"/api/v1/events/{event['id']}/tiers", json=tier, headers=headers)
    ).status_code == 201


async def test_event_cursor_pagination(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    organizer, _ = await make_user(UserRole.EVENT_ORGANIZER)
    for _ in range(5):
        await make_event(organizer.organization_id)

    r = await client.get("/api/v1/events", params={"limit": 2})
    assert r.status_code == 200
    page1 = r.json()
    assert len(page1["items"]) == 2 and page1["next_cursor"]

    r = await client.get(
        "/api/v1/events", params={"limit": 2, "cursor": page1["next_cursor"]}
    )
    page2 = r.json()
    assert len(page2["items"]) == 2
    ids1 = {e["id"] for e in page1["items"]}
    assert ids1.isdisjoint({e["id"] for e in page2["items"]})

    # Third page exhausts the list.
    r = await client.get(
        "/api/v1/events", params={"limit": 2, "cursor": page2["next_cursor"]}
    )
    page3 = r.json()
    assert len(page3["items"]) == 1 and page3["next_cursor"] is None

    assert (
        await client.get("/api/v1/events", params={"cursor": "garbage!"})
    ).status_code == 422


async def test_gdpr_export_and_erasure(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    user, headers = await make_user(email=f"gdpr-{uuid.uuid4().hex[:8]}@test.ems")
    _, tier = await make_event(user.organization_id)
    await client.post(
        "/api/v1/tickets/purchase",
        json={"tier_id": str(tier.id), "quantity": 1},
        headers={**headers, "Idempotency-Key": idem()},
    )

    # Art. 15 export.
    r = await client.get("/api/v1/users/me/export", headers=headers)
    assert r.status_code == 200
    export = r.json()
    assert export["user"]["email"] == user.email
    assert len(export["tickets"]) == 1
    assert len(export["payments"]) == 1

    # Art. 17 erasure.
    assert (await client.delete("/api/v1/users/me", headers=headers)).status_code == 204
    original_email = user.email
    await db_session.refresh(user)
    assert user.anonymized_at is not None
    assert user.email.startswith("anonymized+")
    assert user.full_name is None and user.password_hash is None
    assert not user.is_active

    # Financial records retained (7-year statutory), but PII is gone.
    payments = await db_session.scalar(
        select(User).where(User.email == original_email)
    )
    assert payments is None
    export2 = (await client.get("/api/v1/users/me/export", headers=headers)).json()
    assert len(export2["payments"]) == 1

    # Old credentials no longer work.
    r = await client.post(
        "/api/v1/auth/login", json={"email": original_email, "password": TEST_PASSWORD}
    )
    assert r.status_code == 401


async def test_health(client: httpx.AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
