"""Purchase: free issuance, idempotency, ZERO OVERSELLING under concurrency,
paid checkout via (stubbed) Stripe, signature-verified webhook fulfilment."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from collections.abc import Iterator

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, PaymentStatus, Ticket, TicketStatus
from app.services.stripe_service import StripeService
from tests.conftest import MakeEvent, MakeUser, idem

pytestmark = pytest.mark.db


class StubStripe:
    """Stands in for Stripe — checkout without network, real webhook HMAC check."""

    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}
        self._real = StripeService(
            secret_key=None,
            webhook_secret="whsec_test_secret",
            success_url="https://front.test/success",
            cancel_url="https://front.test/cancel",
        )

    def construct_webhook_event(self, payload: bytes, signature_header: str) -> object:
        return self._real.construct_webhook_event(payload, signature_header)

    async def create_checkout_session(self, **kwargs: object) -> tuple[str, str]:
        session_id = f"cs_test_{uuid.uuid4().hex}"
        url = f"https://checkout.stripe.test/pay/{session_id}"
        self.sessions[session_id] = url
        return session_id, url

    async def checkout_url(self, checkout_session_id: str) -> str | None:
        return self.sessions.get(checkout_session_id)


@pytest.fixture()
def stub_stripe(app: FastAPI) -> Iterator[StubStripe]:
    original = app.state.stripe
    stub = StubStripe()
    app.state.stripe = stub
    yield stub
    app.state.stripe = original


async def _purchase(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    tier_id: uuid.UUID,
    *,
    quantity: int = 1,
    key: str | None = None,
) -> httpx.Response:
    return await client.post(
        "/api/v1/tickets/purchase",
        json={"tier_id": str(tier_id), "quantity": quantity},
        headers={**headers, "Idempotency-Key": key or idem()},
    )


async def test_free_purchase_instant_valid(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id, price_cents=0)

    r = await _purchase(client, headers, tier.id, quantity=2)
    assert r.status_code == 201
    body = r.json()
    assert body["payment_status"] == "succeeded"
    assert body["checkout_url"] is None
    assert len(body["tickets"]) == 2
    assert all(t["status"] == "valid" for t in body["tickets"])


async def test_purchase_requires_idempotency_key(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id)
    r = await client.post(
        "/api/v1/tickets/purchase",
        json={"tier_id": str(tier.id), "quantity": 1},
        headers=headers,
    )
    assert r.status_code == 400


async def test_idempotent_replay_returns_same_payment(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id, capacity=10)
    key = idem()

    first = (await _purchase(client, headers, tier.id, key=key)).json()
    second_resp = await _purchase(client, headers, tier.id, key=key)
    assert second_resp.status_code == 201
    second = second_resp.json()

    assert second["payment_id"] == first["payment_id"]
    assert second["reused"] is True
    await db_session.refresh(tier)
    assert tier.sold_count == 1  # replay did NOT decrement inventory again


async def test_overselling_impossible_under_concurrency(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
) -> None:
    """10 concurrent buyers, capacity 5 → exactly 5 succeed. Non-negotiable (§2)."""
    capacity, attackers = 5, 10
    organizer, _ = await make_user()
    _, tier = await make_event(organizer.organization_id, capacity=capacity)

    buyers = [await make_user() for _ in range(attackers)]
    responses = await asyncio.gather(
        *[_purchase(client, headers, tier.id) for _, headers in buyers]
    )
    statuses = sorted(r.status_code for r in responses)
    assert statuses.count(201) == capacity
    assert statuses.count(409) == attackers - capacity

    await db_session.refresh(tier)
    assert tier.sold_count == capacity
    issued = await db_session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.tier_id == tier.id)
    )
    assert issued == capacity


async def test_quantity_validation(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id)
    assert (await _purchase(client, headers, tier.id, quantity=0)).status_code == 422
    assert (await _purchase(client, headers, tier.id, quantity=11)).status_code == 422


async def test_unpublished_event_not_purchasable(
    client: httpx.AsyncClient, make_user: MakeUser, make_event: MakeEvent
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id, published=False)
    assert (await _purchase(client, headers, tier.id)).status_code == 404


async def test_paid_purchase_returns_checkout_and_webhook_fulfills(
    client: httpx.AsyncClient,
    app: FastAPI,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
    stub_stripe: StubStripe,
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id, price_cents=2500)

    r = await _purchase(client, headers, tier.id, quantity=2)
    assert r.status_code == 201
    body = r.json()
    assert body["payment_status"] == "pending"
    assert body["amount_cents"] == 5000
    assert body["checkout_url"].startswith("https://checkout.stripe.test/")
    assert all(t["status"] == "created" for t in body["tickets"])

    payment = await db_session.get(Payment, uuid.UUID(body["payment_id"]))
    assert payment is not None and payment.stripe_checkout_session_id is not None

    # Stripe calls back — signed with the webhook secret (HMAC, §2).
    event_payload = json.dumps(
        {
            "id": f"evt_{uuid.uuid4().hex}",
            "object": "event",
            "api_version": "2026-01-01",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": payment.stripe_checkout_session_id,
                    "object": "checkout.session",
                    "payment_intent": f"pi_{uuid.uuid4().hex}",
                }
            },
        }
    )
    r = await client.post(
        "/api/v1/webhooks/stripe",
        content=event_payload,
        headers={
            "Stripe-Signature": _stripe_signature(event_payload, "whsec_test_secret"),
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200 and r.json()["handled"] is True

    await db_session.refresh(payment)
    assert payment.status is PaymentStatus.SUCCEEDED
    tickets = (
        await db_session.scalars(select(Ticket).where(Ticket.payment_id == payment.id))
    ).all()
    assert all(t.status is TicketStatus.VALID for t in tickets)


async def test_webhook_rejects_missing_or_bad_signature(client: httpx.AsyncClient) -> None:
    payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}})
    r = await client.post(
        "/api/v1/webhooks/stripe", content=payload, headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 400
    r = await client.post(
        "/api/v1/webhooks/stripe",
        content=payload,
        headers={
            "Stripe-Signature": "t=123,v1=deadbeef",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 400


async def test_release_checkout_frees_inventory(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    make_user: MakeUser,
    make_event: MakeEvent,
    stub_stripe: StubStripe,
) -> None:
    user, headers = await make_user()
    _, tier = await make_event(user.organization_id, price_cents=1000, capacity=3)
    body = (await _purchase(client, headers, tier.id, quantity=2)).json()

    await db_session.refresh(tier)
    assert tier.sold_count == 2  # reserved during checkout

    payment = await db_session.get(Payment, uuid.UUID(body["payment_id"]))
    assert payment is not None

    event_payload = json.dumps(
        {
            "id": f"evt_{uuid.uuid4().hex}",
            "object": "event",
            "api_version": "2026-01-01",
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "id": payment.stripe_checkout_session_id,
                    "object": "checkout.session",
                }
            },
        }
    )
    r = await client.post(
        "/api/v1/webhooks/stripe",
        content=event_payload,
        headers={
            "Stripe-Signature": _stripe_signature(event_payload, "whsec_test_secret"),
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200 and r.json()["handled"] is True

    await db_session.refresh(tier)
    assert tier.sold_count == 0  # inventory released
    await db_session.refresh(payment)
    assert payment.status is PaymentStatus.FAILED


def _stripe_signature(payload: str, secret: str) -> str:
    ts = int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"
