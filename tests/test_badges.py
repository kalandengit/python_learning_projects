"""Badges: issue (RBAC/IDOR), zone ABAC, instant toggle, validity window."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Badge, UserRole
from tests.conftest import MakeEvent, MakeUser

pytestmark = pytest.mark.db


async def _issue_badge(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    event_id: uuid.UUID,
    *,
    badge_type: str = "SECURITY_STAFF",
    zones: list[str] | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> httpx.Response:
    now = datetime.now(UTC)
    return await client.post(
        "/api/v1/badges",
        json={
            "event_id": str(event_id),
            "holder_name": "Guard Alice",
            "type": badge_type,
            "access_zones": zones if zones is not None else ["backstage"],
            "valid_from": (valid_from or now - timedelta(hours=1)).isoformat(),
            "valid_until": (valid_until or now + timedelta(hours=8)).isoformat(),
        },
        headers=headers,
    )


def _badge_qr(app: FastAPI, badge_id: str, event_id: uuid.UUID) -> str:
    qr_data: str = app.state.qr_service.issue(
        _tokens[badge_id], event_id, uuid.UUID(badge_id)
    )
    return qr_data


_tokens: dict[str, str] = {}


async def _remember_token(db_session: AsyncSession, badge_id: str) -> None:
    badge = await db_session.get(Badge, uuid.UUID(badge_id))
    assert badge is not None
    _tokens[badge_id] = badge.qr_token


async def _validate(
    client: httpx.AsyncClient, headers: dict[str, str], qr_data: str, zone: str | None
) -> httpx.Response:
    return await client.post(
        "/api/v1/badges/validate",
        json={"qr_data": qr_data, "device_id": "gate-2", "zone": zone},
        headers=headers,
    )


async def test_issue_requires_organizer_and_own_org(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    organizer, o_headers = await make_user(UserRole.EVENT_ORGANIZER)
    event, _ = await make_event(organizer.organization_id)

    _, a_headers = await make_user()
    assert (await _issue_badge(client, a_headers, event.id)).status_code == 403

    _, other_headers = await make_user(UserRole.EVENT_ORGANIZER)
    assert (await _issue_badge(client, other_headers, event.id)).status_code == 404

    assert (await _issue_badge(client, o_headers, event.id)).status_code == 201


async def test_zone_abac(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    organizer, o_headers = await make_user(UserRole.EVENT_ORGANIZER)
    event, _ = await make_event(organizer.organization_id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    badge = (await _issue_badge(client, o_headers, event.id, zones=["backstage"])).json()
    await _remember_token(db_session, badge["id"])
    qr = _badge_qr(app, badge["id"], event.id)

    assert (await _validate(client, s_headers, qr, "backstage")).status_code == 200
    assert (await _validate(client, s_headers, qr, "vip")).status_code == 422
    assert (await _validate(client, s_headers, qr, None)).status_code == 422


async def test_management_team_all_access(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    organizer, o_headers = await make_user(UserRole.EVENT_ORGANIZER)
    event, _ = await make_event(organizer.organization_id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    badge = (
        await _issue_badge(
            client, o_headers, event.id, badge_type="MANAGEMENT_TEAM", zones=[]
        )
    ).json()
    await _remember_token(db_session, badge["id"])
    qr = _badge_qr(app, badge["id"], event.id)

    for zone in ("backstage", "vip", "server-room", None):
        assert (await _validate(client, s_headers, qr, zone)).status_code == 200


async def test_toggle_deactivates_instantly(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    organizer, o_headers = await make_user(UserRole.EVENT_ORGANIZER)
    event, _ = await make_event(organizer.organization_id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    badge = (await _issue_badge(client, o_headers, event.id)).json()
    await _remember_token(db_session, badge["id"])
    qr = _badge_qr(app, badge["id"], event.id)
    assert (await _validate(client, s_headers, qr, "backstage")).status_code == 200

    r = await client.patch(f"/api/v1/badges/{badge['id']}/toggle", headers=o_headers)
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await _validate(client, s_headers, qr, "backstage")).status_code == 422

    # Toggle back on.
    r = await client.patch(f"/api/v1/badges/{badge['id']}/toggle", headers=o_headers)
    assert r.status_code == 200 and r.json()["is_active"] is True
    assert (await _validate(client, s_headers, qr, "backstage")).status_code == 200


async def test_validity_window_enforced(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    organizer, o_headers = await make_user(UserRole.EVENT_ORGANIZER)
    event, _ = await make_event(organizer.organization_id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    now = datetime.now(UTC)
    badge = (
        await _issue_badge(
            client,
            o_headers,
            event.id,
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(days=1),  # expired yesterday
        )
    ).json()
    await _remember_token(db_session, badge["id"])
    qr = _badge_qr(app, badge["id"], event.id)
    assert (await _validate(client, s_headers, qr, "backstage")).status_code == 422
