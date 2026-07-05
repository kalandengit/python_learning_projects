"""Badges: issue (organizer), instant toggle, zone-ABAC validation (scanner)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.deps import (
    get_app_settings,
    get_qr_service,
    get_rate_limiter,
    get_signer,
    require_organizer,
    require_scanner,
)
from app.core.pqc import HybridSigner
from app.core.rate_limit import RateLimiter
from app.core.security import AuthContext
from app.db import get_session
from app.models import Badge, Event, ScanResult
from app.schemas.badges import (
    BadgeCreate,
    BadgeOut,
    BadgeValidateRequest,
    BadgeValidateResponse,
)
from app.services import badge_service
from app.services.qr_service import QRService

router = APIRouter(prefix="/badges", tags=["badges"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("", response_model=list[BadgeOut])
async def list_badges(
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    event_id: Annotated[uuid.UUID, Query()],
) -> list[BadgeOut]:
    event = await session.get(Event, event_id)
    # IDOR: an organizer only ever sees badges for their own org's events.
    if event is None or event.organization_id != auth.org_id:
        raise _NOT_FOUND
    badges = (
        await session.scalars(
            select(Badge)
            .where(Badge.event_id == event_id, Badge.organization_id == auth.org_id)
            .order_by(Badge.created_at.desc())
        )
    ).all()
    return [BadgeOut.model_validate(b) for b in badges]


@router.post("", response_model=BadgeOut, status_code=status.HTTP_201_CREATED)
async def create_badge(
    body: BadgeCreate,
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    signer: Annotated[HybridSigner, Depends(get_signer)],
) -> BadgeOut:
    event = await session.get(Event, body.event_id)
    # IDOR: badges can only be issued for the caller's own organization.
    if event is None or event.organization_id != auth.org_id:
        raise _NOT_FOUND
    badge = await badge_service.issue_badge(
        session,
        actor=auth,
        event_id=body.event_id,
        holder_name=body.holder_name,
        badge_type=body.type,
        access_zones=body.access_zones,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        user_id=body.user_id,
        nfc_uid=body.nfc_uid,
        signer=signer,
    )
    return BadgeOut.model_validate(badge)


@router.patch("/{badge_id}/toggle", response_model=BadgeOut)
async def toggle_badge(
    badge_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BadgeOut:
    try:
        badge = await badge_service.toggle_badge(session, badge_id=badge_id, actor=auth)
    except badge_service.BadgeNotFound as exc:
        raise _NOT_FOUND from exc
    return BadgeOut.model_validate(badge)


@router.post("/validate", response_model=BadgeValidateResponse)
async def validate_badge(
    body: BadgeValidateRequest,
    scanner: Annotated[AuthContext, Depends(require_scanner)],
    session: Annotated[AsyncSession, Depends(get_session)],
    qr: Annotated[QRService, Depends(get_qr_service)],
    signer: Annotated[HybridSigner, Depends(get_signer)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> BadgeValidateResponse:
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
        validation = await badge_service.validate_badge(
            session,
            qr_data=body.qr_data,
            zone=body.zone,
            device_id=body.device_id,
            scanner=scanner,
            qr_service=qr,
            signer=signer,
        )
    except badge_service.BadgeRejected as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Badge not valid"
        ) from exc

    return BadgeValidateResponse(
        result=ScanResult.ACCEPTED,
        badge_id=validation.badge_id,
        badge_type=validation.badge_type,
        holder_name=validation.holder_name,
        zone=validation.zone,
    )
