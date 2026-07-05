"""ICS calendar feed: token issue/revoke (authenticated) and public feed."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import CurrentUser, enforce_rate_limit, get_current_user, ics_limiter
from ..models import IcsToken, Shift
from ..models.base import ensure_aware, utcnow
from ..security import generate_opaque_token, hash_token
from ..services.ics import render_calendar

settings = get_settings()
router = APIRouter(prefix="/ics", tags=["ics"])


@router.post("/token", status_code=201)
def create_ics_token(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Issue a fresh feed token, revoking any existing ones for this user."""
    for existing in db.scalars(
        select(IcsToken).where(
            IcsToken.user_id == user.id, IcsToken.revoked_at.is_(None)
        )
    ):
        existing.revoked_at = utcnow()

    raw = generate_opaque_token()
    token = IcsToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=utcnow() + timedelta(days=settings.ics_token_ttl_days),
    )
    db.add(token)
    db.commit()
    return {"feed_url": f"/ics/feed/{raw}.ics", "token": raw}


@router.post("/token/revoke", status_code=204)
def revoke_ics_tokens(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    for token in db.scalars(
        select(IcsToken).where(
            IcsToken.user_id == user.id, IcsToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/feed/{raw_token}.ics")
def ics_feed(raw_token: str, request: Request, db: Session = Depends(get_db)) -> Response:
    """Public feed endpoint consumed by calendar clients; auth is the token."""
    enforce_rate_limit(ics_limiter, f"ics:{raw_token[:16]}", settings.rate_limit_ics)

    token = db.scalar(select(IcsToken).where(IcsToken.token_hash == hash_token(raw_token)))
    if token is None or token.revoked_at is not None or ensure_aware(token.expires_at) < utcnow():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Feed not found")

    shifts = list(
        db.scalars(
            select(Shift).where(
                Shift.tenant_id == token.tenant_id,
                Shift.user_id == token.user_id,
                Shift.published.is_(True),
                Shift.deleted_at.is_(None),
            ).order_by(Shift.starts_at)
        )
    )
    body = render_calendar(shifts, calendar_name="StaffHub Shifts")
    return Response(content=body, media_type="text/calendar")
