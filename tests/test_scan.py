"""Entry scan: atomic accept, duplicate → 409, tamper/PQC rejection,
and the every-scan-is-logged guarantee (§2)."""

from __future__ import annotations

import time
import uuid

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ScanLog, ScanResult, Ticket, TicketStatus, UserRole
from tests.conftest import MakeEvent, MakeUser, idem

pytestmark = pytest.mark.db


async def _buy_ticket(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    headers: dict[str, str],
    tier_id: uuid.UUID,
) -> Ticket:
    r = await client.post(
        "/api/v1/tickets/purchase",
        json={"tier_id": str(tier_id), "quantity": 1},
        headers={**headers, "Idempotency-Key": idem()},
    )
    assert r.status_code == 201
    ticket_id = uuid.UUID(r.json()["tickets"][0]["id"])
    ticket = await db_session.get(Ticket, ticket_id)
    assert ticket is not None
    return ticket


def _qr_for(app: FastAPI, ticket: Ticket, *, now: float | None = None) -> str:
    qr_data: str = app.state.qr_service.issue(
        ticket.qr_token, ticket.event_id, ticket.owner_id, now=now
    )
    return qr_data


async def _validate(
    client: httpx.AsyncClient, headers: dict[str, str], qr_data: str, device: str = "gate-1"
) -> httpx.Response:
    return await client.post(
        "/api/v1/tickets/validate",
        json={"qr_data": qr_data, "device_id": device, "zone": "main"},
        headers=headers,
    )


async def _scan_results(db_session: AsyncSession, ticket_id: uuid.UUID) -> list[ScanResult]:
    logs = (
        await db_session.scalars(
            select(ScanLog).where(ScanLog.subject_id == ticket_id).order_by(ScanLog.scanned_at)
        )
    ).all()
    return [log.result for log in logs]


async def test_scan_accept_then_duplicate_409(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    r = await _validate(client, s_headers, _qr_for(app, ticket))
    assert r.status_code == 200
    assert r.json()["result"] == "accepted"
    assert r.json()["used_at"] is not None

    # Same QR again → duplicate, 409 (§2).
    r = await _validate(client, s_headers, _qr_for(app, ticket))
    assert r.status_code == 409

    await db_session.refresh(ticket)
    assert ticket.status is TicketStatus.USED
    assert await _scan_results(db_session, ticket.id) == [
        ScanResult.ACCEPTED,
        ScanResult.DUPLICATE,
    ]


async def test_tampered_qr_rejected_and_logged(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)
    _, s_headers = await make_user(UserRole.BOX_OFFICE_STAFF)

    qr_data = _qr_for(app, ticket)
    head, _, mac = qr_data.rpartition(".")
    tampered = f"{head}." + ("A" if mac[0] != "A" else "B") + mac[1:]

    r = await _validate(client, s_headers, tampered)
    assert r.status_code == 422

    await db_session.refresh(ticket)
    assert ticket.status is TicketStatus.VALID  # untouched

    rejected = (
        await db_session.scalars(
            select(ScanLog).where(ScanLog.result == ScanResult.REJECTED)
        )
    ).all()
    assert any(log.reason == "envelope:bad_mac" for log in rejected)


async def test_pqc_signature_tamper_rejected(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    """Flipping a byte of the stored hybrid signature must void the ticket."""
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)

    assert ticket.pqc_signature is not None
    corrupted = bytearray(ticket.pqc_signature)
    corrupted[10] ^= 0xFF
    ticket.pqc_signature = bytes(corrupted)
    await db_session.commit()

    _, s_headers = await make_user(UserRole.SECURITY_GUARD)
    r = await _validate(client, s_headers, _qr_for(app, ticket))
    assert r.status_code == 422

    logs = await db_session.scalars(
        select(ScanLog).where(ScanLog.subject_id == ticket.id)
    )
    assert [log.reason for log in logs] == ["pqc_signature_invalid"]


async def test_stale_qr_rejected(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)

    stale = _qr_for(app, ticket, now=time.time() - 3600)  # client stopped refreshing
    r = await _validate(client, s_headers, stale)
    assert r.status_code == 422


async def test_attendee_cannot_validate(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)
    r = await _validate(client, a_headers, _qr_for(app, ticket))
    assert r.status_code == 403  # ATTENDEE is not a scanner role


async def test_qr_png_owner_only_and_no_store(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    attendee, a_headers = await make_user()
    _, tier = await make_event(attendee.organization_id)
    ticket = await _buy_ticket(client, db_session, a_headers, tier.id)

    r = await client.get(f"/api/v1/tickets/{ticket.id}/qr", headers=a_headers)
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"
    assert r.content.startswith(b"\x89PNG")

    _, other_headers = await make_user()
    r = await client.get(f"/api/v1/tickets/{ticket.id}/qr", headers=other_headers)
    assert r.status_code == 404  # IDOR: not the owner, not even a 403 hint


async def test_scan_rate_limit_per_device(
    client: httpx.AsyncClient,
    app: FastAPI,
    make_user: MakeUser,
) -> None:
    _, s_headers = await make_user(UserRole.SECURITY_GUARD)
    settings = app.state.settings
    device = f"dev-{uuid.uuid4().hex[:8]}"
    limit = settings.scan_rate_per_device_per_minute
    for _ in range(limit):
        r = await _validate(client, s_headers, "EMS3.bogus.bogus", device=device)
        assert r.status_code == 422
    r = await _validate(client, s_headers, "EMS3.bogus.bogus", device=device)
    assert r.status_code == 429
    assert "retry-after" in r.headers
