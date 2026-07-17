"""Registration and login."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.limits import limiter
from app.logging_conf import get_logger
from app.models import (
    RefreshSession,
    TrainingSample,
    Transcription,
    TranscriptionJob,
    TranscriptSegment,
    User,
)
from app.schemas import PasswordConfirm, TokenResponse, UserCreate, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    new_refresh_token,
    refresh_hash,
    verify_dummy,
    verify_password,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(request: Request, body: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == body.username))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # The pre-check is user-friendly; the constraint handles concurrent
        # registrations that race between SELECT and INSERT.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken") from None
    db.refresh(user)
    logger.info("event=user_registered user_id=%s", user.id)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/hour")
def login(
    request: Request, body: UserCreate, response: Response, db: Session = Depends(get_db)
):
    user = db.scalar(select(User).where(User.username == body.username))
    # Same error AND same work for unknown user and bad password: no username
    # enumeration via response body or response time.
    if user is None:
        verify_dummy(body.password)
        ok = False
    else:
        ok = verify_password(body.password, user.password_hash)
    if not ok:
        logger.warning("event=login_failed username_hash=%s", hash(body.username))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    settings = get_settings()
    refresh, token_hash = new_refresh_token()
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    response.set_cookie(
        "nko_refresh",
        refresh,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/api/auth",
    )
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in_minutes=settings.access_token_minutes,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("60/hour")
def refresh_access(
    request: Request,
    response: Response,
    nko_refresh: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not nko_refresh:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh session required")
    row = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == refresh_hash(nko_refresh))
    )
    now = datetime.now(UTC)
    expires = row.expires_at.replace(tzinfo=UTC) if row and row.expires_at.tzinfo is None else (
        row.expires_at if row else now
    )
    if row is None or row.revoked or expires <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh session expired")
    row.revoked = True
    token, token_hash = new_refresh_token()
    settings = get_settings()
    db.add(
        RefreshSession(
            user_id=row.user_id,
            token_hash=token_hash,
            expires_at=now + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    response.set_cookie(
        "nko_refresh",
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/api/auth",
    )
    return TokenResponse(
        access_token=create_access_token(row.user_id),
        expires_in_minutes=settings.access_token_minutes,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    nko_refresh: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if nko_refresh:
        row = db.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == refresh_hash(nko_refresh))
        )
        if row:
            row.revoked = True
            db.commit()
    response.delete_cookie("nko_refresh", path="/api/auth")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    body: PasswordConfirm,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Password confirmation failed")
    transcription_ids = list(
        db.scalars(select(Transcription.id).where(Transcription.user_id == user.id))
    )
    for sample in db.scalars(select(TrainingSample).where(TrainingSample.user_id == user.id)):
        Path(sample.audio_path).unlink(missing_ok=True)
        db.delete(sample)
    db.execute(delete(TranscriptionJob).where(TranscriptionJob.user_id == user.id))
    if transcription_ids:
        db.execute(
            delete(TranscriptSegment).where(
                TranscriptSegment.transcription_id.in_(transcription_ids)
            )
        )
    db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    db.execute(delete(Transcription).where(Transcription.user_id == user.id))
    db.delete(user)
    db.commit()
    response.delete_cookie("nko_refresh", path="/api/auth")
