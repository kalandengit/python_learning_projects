"""Ticket purchase and entry scan — the two concurrency-critical paths (§2).

* Purchase locks the tier row with ``SELECT … FOR UPDATE`` before touching
  ``sold_count`` — zero overselling, non-negotiable.
* Entry scan is a single atomic ``UPDATE … WHERE status='valid' RETURNING``;
  a second scan finds no row and is logged + rejected with 409.
* Every scan is logged, accepted AND rejected (evacuation tracking).

Neither invariant may be "simplified" (§7.3).
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pqc import HybridSigner
from app.core.security import AuthContext
from app.models import (
    Event,
    Payment,
    PaymentStatus,
    ScanLog,
    ScanResult,
    ScanSubject,
    Ticket,
    TicketStatus,
    TicketStatusHistory,
    TicketTier,
)
from app.services.qr_service import QRInvalid, QRService, owner_hash, static_payload
from app.services.stripe_service import StripeService


class PurchaseError(Exception):
    """Base for purchase failures; `code` is safe to surface to clients."""

    code = "purchase_failed"
    http_status = 400


class TierNotFound(PurchaseError):
    code = "tier_not_found"
    http_status = 404


class EventNotOnSale(PurchaseError):
    code = "event_not_on_sale"


class SoldOut(PurchaseError):
    code = "sold_out"
    http_status = 409


class QuantityInvalid(PurchaseError):
    code = "quantity_invalid"
    http_status = 422


MAX_TICKETS_PER_PURCHASE = 10


@dataclass(frozen=True)
class PurchaseResult:
    payment: Payment
    tickets: list[Ticket]
    checkout_url: str | None
    reused: bool  # True when the Idempotency-Key matched an earlier purchase


@dataclass(frozen=True)
class ScanOutcome:
    result: ScanResult
    ticket_id: uuid.UUID | None
    event_id: uuid.UUID | None
    used_at: datetime | None
    reason: str | None


def _new_qr_token() -> str:
    return secrets.token_urlsafe(32)


async def purchase(
    session: AsyncSession,
    *,
    buyer: AuthContext,
    buyer_email: str,
    tier_id: uuid.UUID,
    quantity: int,
    idempotency_key: str,
    signer: HybridSigner,
    stripe: StripeService,
) -> PurchaseResult:
    if not 1 <= quantity <= MAX_TICKETS_PER_PURCHASE:
        raise QuantityInvalid

    # Idempotent replay: same user + Idempotency-Key returns the original outcome.
    existing = await session.scalar(
        select(Payment).where(
            Payment.user_id == buyer.user_id, Payment.idempotency_key == idempotency_key
        )
    )
    if existing is not None:
        prior = list(
            await session.scalars(select(Ticket).where(Ticket.payment_id == existing.id))
        )
        url = None
        if existing.status is PaymentStatus.PENDING and existing.stripe_checkout_session_id:
            url = await stripe.checkout_url(existing.stripe_checkout_session_id)
        return PurchaseResult(payment=existing, tickets=prior, checkout_url=url, reused=True)

    # Inventory invariant: lock the tier row before reading/writing sold_count.
    tier = await session.scalar(
        select(TicketTier).where(TicketTier.id == tier_id).with_for_update()
    )
    if tier is None:
        raise TierNotFound
    event = await session.get(Event, tier.event_id)
    if event is None or not event.is_published:
        raise TierNotFound  # unpublished events are not enumerable

    now = datetime.now(UTC)
    if (tier.sales_starts_at and now < tier.sales_starts_at) or (
        tier.sales_ends_at and now > tier.sales_ends_at
    ):
        raise EventNotOnSale
    if now > event.ends_at:
        raise EventNotOnSale
    if tier.capacity - tier.sold_count < quantity:
        raise SoldOut

    # Reserve inventory for FREE and PAID alike; released if checkout fails.
    tier.sold_count += quantity
    free = tier.price_cents == 0

    payment = Payment(
        user_id=buyer.user_id,
        event_id=event.id,
        tier_id=tier.id,
        quantity=quantity,
        amount_cents=tier.price_cents * quantity,
        currency=tier.currency,
        status=PaymentStatus.SUCCEEDED if free else PaymentStatus.PENDING,
        idempotency_key=idempotency_key,
    )
    session.add(payment)
    await session.flush()

    tickets: list[Ticket] = []
    initial_status = TicketStatus.VALID if free else TicketStatus.CREATED
    for _ in range(quantity):
        token = _new_qr_token()
        ticket = Ticket(
            tier_id=tier.id,
            event_id=event.id,
            owner_id=buyer.user_id,
            payment_id=payment.id,
            status=initial_status,
            qr_token=token,
            pqc_signature=signer.sign(static_payload(token, event.id, buyer.user_id)),
        )
        session.add(ticket)
        tickets.append(ticket)
    await session.flush()

    for ticket in tickets:
        session.add(
            TicketStatusHistory(
                ticket_id=ticket.id,
                from_status=None,
                to_status=TicketStatus.CREATED,
                reason="purchase",
                actor_id=buyer.user_id,
            )
        )
        if free:
            session.add(
                TicketStatusHistory(
                    ticket_id=ticket.id,
                    from_status=TicketStatus.CREATED,
                    to_status=TicketStatus.VALID,
                    reason="free_ticket_issued",
                    actor_id=buyer.user_id,
                )
            )

    checkout_url: str | None = None
    if not free:
        session_id, checkout_url = await stripe.create_checkout_session(
            payment_id=payment.id,
            idempotency_key=idempotency_key,
            product_name=f"{event.title} — {tier.name}",
            unit_amount_cents=tier.price_cents,
            currency=tier.currency,
            quantity=quantity,
            customer_email=buyer_email,
        )
        payment.stripe_checkout_session_id = session_id

    await session.commit()
    return PurchaseResult(payment=payment, tickets=tickets, checkout_url=checkout_url, reused=False)


async def _transition_payment_tickets(
    session: AsyncSession,
    payment: Payment,
    *,
    from_status: TicketStatus,
    to_status: TicketStatus,
    reason: str,
) -> int:
    result = await session.execute(
        update(Ticket)
        .where(Ticket.payment_id == payment.id, Ticket.status == from_status)
        .values(status=to_status)
        .returning(Ticket.id)
    )
    ids = [row[0] for row in result]
    for ticket_id in ids:
        session.add(
            TicketStatusHistory(
                ticket_id=ticket_id, from_status=from_status, to_status=to_status, reason=reason
            )
        )
    return len(ids)


async def fulfill_checkout(
    session: AsyncSession, *, checkout_session_id: str, payment_intent_id: str | None
) -> bool:
    """checkout.session.completed → payment succeeded, tickets valid. Idempotent."""
    payment = await session.scalar(
        select(Payment)
        .where(Payment.stripe_checkout_session_id == checkout_session_id)
        .with_for_update()
    )
    if payment is None or payment.status is not PaymentStatus.PENDING:
        return False
    payment.status = PaymentStatus.SUCCEEDED
    if payment_intent_id:
        payment.stripe_payment_intent_id = payment_intent_id
    await _transition_payment_tickets(
        session,
        payment,
        from_status=TicketStatus.CREATED,
        to_status=TicketStatus.VALID,
        reason="payment_succeeded",
    )
    await session.commit()
    return True


async def release_checkout(
    session: AsyncSession, *, checkout_session_id: str, reason: str
) -> bool:
    """Expired/failed checkout → tickets expired, inventory released. Idempotent."""
    payment = await session.scalar(
        select(Payment)
        .where(Payment.stripe_checkout_session_id == checkout_session_id)
        .with_for_update()
    )
    if payment is None or payment.status is not PaymentStatus.PENDING:
        return False
    payment.status = PaymentStatus.FAILED
    released = await _transition_payment_tickets(
        session,
        payment,
        from_status=TicketStatus.CREATED,
        to_status=TicketStatus.EXPIRED,
        reason=reason,
    )
    if released:
        tier = await session.scalar(
            select(TicketTier).where(TicketTier.id == payment.tier_id).with_for_update()
        )
        if tier is not None:
            tier.sold_count = max(tier.sold_count - released, 0)
    await session.commit()
    return True


async def refund_payment(session: AsyncSession, *, payment_intent_id: str) -> bool:
    """charge.refunded → unused tickets refunded, inventory released. Idempotent."""
    payment = await session.scalar(
        select(Payment)
        .where(Payment.stripe_payment_intent_id == payment_intent_id)
        .with_for_update()
    )
    if payment is None or payment.status is PaymentStatus.REFUNDED:
        return False
    payment.status = PaymentStatus.REFUNDED
    refunded = await _transition_payment_tickets(
        session,
        payment,
        from_status=TicketStatus.VALID,
        to_status=TicketStatus.REFUNDED,
        reason="stripe_refund",
    )
    if refunded:
        tier = await session.scalar(
            select(TicketTier).where(TicketTier.id == payment.tier_id).with_for_update()
        )
        if tier is not None:
            tier.sold_count = max(tier.sold_count - refunded, 0)
    await session.commit()
    return True


class ScanRejected(Exception):
    """Envelope/ticket invalid — logged; client gets a generic message."""

    http_status = 422


class DuplicateScan(Exception):
    """Ticket already used — 409 (§2)."""

    http_status = 409


async def _log_scan(
    session: AsyncSession,
    *,
    result: ScanResult,
    reason: str | None,
    subject_id: uuid.UUID | None,
    event_id: uuid.UUID | None,
    device_id: str,
    scanner: AuthContext,
    zone: str | None,
) -> None:
    session.add(
        ScanLog(
            subject_type=ScanSubject.TICKET,
            subject_id=subject_id,
            event_id=event_id,
            result=result,
            reason=reason,
            zone=zone,
            device_id=device_id,
            scanned_by=scanner.user_id,
        )
    )
    await session.commit()


async def scan_ticket(
    session: AsyncSession,
    *,
    qr_data: str,
    device_id: str,
    zone: str | None,
    scanner: AuthContext,
    qr_service: QRService,
    signer: HybridSigner,
) -> ScanOutcome:
    try:
        envelope = qr_service.verify(qr_data)
    except QRInvalid as exc:
        await _log_scan(
            session,
            result=ScanResult.REJECTED,
            reason=f"envelope:{exc.reason}",
            subject_id=None,
            event_id=None,
            device_id=device_id,
            scanner=scanner,
            zone=zone,
        )
        raise ScanRejected from exc

    ticket = await session.scalar(select(Ticket).where(Ticket.qr_token == envelope.qr_token))
    if (
        ticket is None
        or ticket.event_id != envelope.event_id
        or owner_hash(ticket.owner_id) != envelope.owner_hash
    ):
        await _log_scan(
            session,
            result=ScanResult.REJECTED,
            reason="unknown_or_mismatched_ticket",
            subject_id=ticket.id if ticket else None,
            event_id=envelope.event_id,
            device_id=device_id,
            scanner=scanner,
            zone=zone,
        )
        raise ScanRejected

    # Hybrid PQC verification of the static payload (tamper defense in depth).
    payload = static_payload(envelope.qr_token, ticket.event_id, ticket.owner_id)
    if ticket.pqc_signature is None or not signer.verify(payload, ticket.pqc_signature):
        await _log_scan(
            session,
            result=ScanResult.REJECTED,
            reason="pqc_signature_invalid",
            subject_id=ticket.id,
            event_id=ticket.event_id,
            device_id=device_id,
            scanner=scanner,
            zone=zone,
        )
        raise ScanRejected

    # Atomic single-statement transition — the concurrency invariant (§2).
    now = datetime.now(UTC)
    row = (
        await session.execute(
            update(Ticket)
            .where(Ticket.id == ticket.id, Ticket.status == TicketStatus.VALID)
            .values(status=TicketStatus.USED, used_at=now)
            .returning(Ticket.id, Ticket.used_at)
        )
    ).first()

    if row is None:
        await session.rollback()
        current = await session.scalar(select(Ticket.status).where(Ticket.id == ticket.id))
        if current is TicketStatus.USED:
            await _log_scan(
                session,
                result=ScanResult.DUPLICATE,
                reason="already_used",
                subject_id=ticket.id,
                event_id=ticket.event_id,
                device_id=device_id,
                scanner=scanner,
                zone=zone,
            )
            raise DuplicateScan
        await _log_scan(
            session,
            result=ScanResult.REJECTED,
            reason=f"status_{current.value if current else 'missing'}",
            subject_id=ticket.id,
            event_id=ticket.event_id,
            device_id=device_id,
            scanner=scanner,
            zone=zone,
        )
        raise ScanRejected

    session.add(
        TicketStatusHistory(
            ticket_id=ticket.id,
            from_status=TicketStatus.VALID,
            to_status=TicketStatus.USED,
            reason="entry_scan",
            actor_id=scanner.user_id,
        )
    )
    session.add(
        ScanLog(
            subject_type=ScanSubject.TICKET,
            subject_id=ticket.id,
            event_id=ticket.event_id,
            result=ScanResult.ACCEPTED,
            reason=None,
            zone=zone,
            device_id=device_id,
            scanned_by=scanner.user_id,
        )
    )
    await session.commit()
    return ScanOutcome(
        result=ScanResult.ACCEPTED,
        ticket_id=ticket.id,
        event_id=ticket.event_id,
        used_at=row[1],
        reason=None,
    )
