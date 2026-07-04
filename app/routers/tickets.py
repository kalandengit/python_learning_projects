"""Tickets: purchase (Idempotency-Key), mine, QR PNG (no-store), validate."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.deps import (
    get_app_settings,
    get_auth,
    get_qr_service,
    get_rate_limiter,
    get_signer,
    get_stripe,
    require_scanner,
)
from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.core.pqc import HybridSigner
from app.core.rate_limit import RateLimiter
from app.core.security import AuthContext
from app.db import get_session
from app.models import Ticket, TicketStatus, User
from app.schemas.tickets import (
    PurchaseRequest,
    PurchaseResponse,
    TicketOut,
    TicketPage,
    ValidateRequest,
    ValidateResponse,
)
from app.services import ticket_service
from app.services.qr_service import QRService
from app.services.stripe_service import StripeService

router = APIRouter(prefix="/tickets", tags=["tickets"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase(
    body: PurchaseRequest,
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    signer: Annotated[HybridSigner, Depends(get_signer)],
    stripe: Annotated[StripeService, Depends(get_stripe)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PurchaseResponse:
    if not idempotency_key or len(idempotency_key) > 255:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required"
        )

    decision = await limiter.hit(
        f"purchase:user:{auth.user_id}",
        limit=settings.purchase_rate_per_user_per_hour,
        window_seconds=3600,
    )
    if not decision.allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many purchases",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    user = await session.get(User, auth.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        result = await ticket_service.purchase(
            session,
            buyer=auth,
            buyer_email=user.email,
            tier_id=body.tier_id,
            quantity=body.quantity,
            idempotency_key=idempotency_key,
            signer=signer,
            stripe=stripe,
        )
    except ticket_service.PurchaseError as exc:
        raise HTTPException(exc.http_status, detail=exc.code) from exc

    return PurchaseResponse(
        payment_id=result.payment.id,
        payment_status=result.payment.status,
        amount_cents=result.payment.amount_cents,
        currency=result.payment.currency,
        tickets=[TicketOut.model_validate(t) for t in result.tickets],
        checkout_url=result.checkout_url,
        reused=result.reused,
    )


@router.get("/mine", response_model=TicketPage)
async def my_tickets(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TicketPage:
    query = (
        select(Ticket)
        .where(Ticket.owner_id == auth.user_id)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .limit(limit + 1)
    )
    if cursor is not None:
        try:
            created_at, last_id = decode_cursor(cursor)
        except CursorError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid cursor"
            ) from exc
        query = query.where(tuple_(Ticket.created_at, Ticket.id) < (created_at, last_id))

    tickets = list((await session.scalars(query)).all())
    has_more = len(tickets) > limit
    tickets = tickets[:limit]
    next_cursor = (
        encode_cursor(tickets[-1].created_at, tickets[-1].id) if has_more and tickets else None
    )
    return TicketPage(
        items=[TicketOut.model_validate(t) for t in tickets], next_cursor=next_cursor
    )


@router.get("/{ticket_id}/qr")
async def ticket_qr(
    ticket_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    qr: Annotated[QRService, Depends(get_qr_service)],
) -> Response:
    ticket = await session.get(Ticket, ticket_id)
    # IDOR: only the owner may fetch the QR.
    if ticket is None or ticket.owner_id != auth.user_id:
        raise _NOT_FOUND
    if ticket.status is not TicketStatus.VALID:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Ticket is not valid")
    qr_data = qr.issue(ticket.qr_token, ticket.event_id, ticket.owner_id)
    return Response(
        content=qr.render_png(qr_data),
        media_type="image/png",
        headers={"Cache-Control": "no-store"},  # §2 — QR refreshes ≤60 s
    )


@router.post("/validate", response_model=ValidateResponse)
async def validate_ticket(
    body: ValidateRequest,
    scanner: Annotated[AuthContext, Depends(require_scanner)],
    session: Annotated[AsyncSession, Depends(get_session)],
    qr: Annotated[QRService, Depends(get_qr_service)],
    signer: Annotated[HybridSigner, Depends(get_signer)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ValidateResponse:
    decision = await limiter.hit(
        f"scan:device:{body.device_id}",
        limit=settings.scan_rate_per_device_per_minute,
        window_seconds=60,
    )
    if not decision.allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Scan rate limit exceeded",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    try:
        outcome = await ticket_service.scan_ticket(
            session,
            qr_data=body.qr_data,
            device_id=body.device_id,
            zone=body.zone,
            scanner=scanner,
            qr_service=qr,
            signer=signer,
        )
    except ticket_service.DuplicateScan as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Ticket already used") from exc
    except ticket_service.ScanRejected as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Ticket not valid"
        ) from exc

    return ValidateResponse(
        result=outcome.result,
        ticket_id=outcome.ticket_id,
        event_id=outcome.event_id,
        used_at=outcome.used_at,
    )
