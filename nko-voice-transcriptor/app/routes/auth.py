"""Registration and login."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
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
from app.schemas import LoginRequest, PasswordConfirm, TokenResponse, UserCreate, UserOut
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
    if body.email and db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
    )
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
    request: Request, body: LoginRequest, response: Response, db: Session = Depends(get_db)
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


def _oauth_config(provider: str):
    settings = get_settings()
    if provider == "google":
        return settings.google_client_id, settings.google_client_secret
    if provider == "facebook":
        return settings.facebook_client_id, settings.facebook_client_secret
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown social provider")


def _oauth_callback_url(request: Request, provider: str) -> str:
    base = get_settings().oauth_base_url.rstrip("/") or str(request.base_url).rstrip("/")
    return f"{base}/api/auth/oauth/{provider}/callback"


@router.get("/oauth/providers")
def oauth_providers():
    settings = get_settings()
    return {
        "google": bool(settings.google_client_id and settings.google_client_secret),
        "facebook": bool(settings.facebook_client_id and settings.facebook_client_secret),
    }


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str, request: Request):
    client_id, client_secret = _oauth_config(provider)
    if not client_id or not client_secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Provider is not configured")
    settings = get_settings()
    state = jwt.encode(
        {
            "type": "oauth_state", "provider": provider,
            "nonce": secrets.token_urlsafe(18),
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    callback = _oauth_callback_url(request, provider)
    if provider == "google":
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": client_id, "redirect_uri": callback, "response_type": "code",
            "scope": "openid email profile", "state": state, "prompt": "select_account",
        })
    else:
        url = "https://www.facebook.com/dialog/oauth?" + urlencode({
            "client_id": client_id, "redirect_uri": callback, "response_type": "code",
            "scope": "email,public_profile", "state": state,
        })
    response = RedirectResponse(url)
    response.set_cookie(
        "nko_oauth_state", state, max_age=600, httponly=True,
        secure=settings.secure_cookies, samesite="lax", path="/api/auth/oauth",
    )
    return response


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str,
    state: str,
    nko_oauth_state: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    client_id, client_secret = _oauth_config(provider)
    if not nko_oauth_state or not secrets.compare_digest(state, nko_oauth_state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")
    try:
        payload = jwt.decode(state, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Expired OAuth state") from None
    if payload.get("type") != "oauth_state" or payload.get("provider") != provider:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")
    callback = _oauth_callback_url(request, provider)
    async with httpx.AsyncClient(timeout=20) as client:
        if provider == "google":
            token_response = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": client_id, "client_secret": client_secret,
                "redirect_uri": callback, "grant_type": "authorization_code",
            })
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            profile_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        else:
            token_response = await client.get(
                "https://graph.facebook.com/oauth/access_token",
                params={
                    "client_id": client_id, "client_secret": client_secret,
                    "redirect_uri": callback, "code": code,
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            profile_response = await client.get(
                "https://graph.facebook.com/me",
                params={"fields": "id,first_name,last_name,email", "access_token": access_token},
            )
        profile_response.raise_for_status()
        profile = profile_response.json()
    subject = str(profile.get("sub") or profile.get("id") or "")
    if not subject:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Social profile has no identifier")
    user = db.scalar(select(User).where(
        User.oauth_provider == provider, User.oauth_subject == subject
    ))
    if user is None:
        base = (profile.get("email") or f"{provider}_{subject}").split("@", 1)[0]
        base = "".join(ch for ch in base if ch.isalnum() or ch in "_.-")[:48] or provider
        username = base
        while db.scalar(select(User).where(User.username == username)):
            username = f"{base}_{secrets.token_hex(3)}"
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(40)),
            first_name=profile.get("given_name") or profile.get("first_name"),
            last_name=profile.get("family_name") or profile.get("last_name"),
            email=profile.get("email"),
            oauth_provider=provider,
            oauth_subject=subject,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    settings = get_settings()
    refresh_token, token_hash = new_refresh_token()
    db.add(RefreshSession(
        user_id=user.id, token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    ))
    db.commit()
    response = RedirectResponse("/?oauth=success")
    response.delete_cookie("nko_oauth_state", path="/api/auth/oauth")
    response.set_cookie(
        "nko_refresh", refresh_token, max_age=settings.refresh_token_days * 86400,
        httponly=True, secure=settings.secure_cookies, samesite="strict", path="/api/auth",
    )
    return response


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
