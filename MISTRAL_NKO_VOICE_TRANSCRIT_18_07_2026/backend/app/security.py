"""Passwords, JWTs, refresh-token rotation with reuse detection."""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import RefreshToken, User, utcnow

logger = logging.getLogger("nko.auth")

_hasher = PasswordHasher()
# Verified for unknown accounts so login costs the same whether or not the
# email exists (timing side-channel fix carried over from v1.3.0).
_DUMMY_HASH = _hasher.hash(secrets.token_hex(16))

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash — treat as failure, constant-ish cost
        return False
    return password_hash is not None


def _encode(claims: dict, lifetime: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {**claims, "iat": now, "exp": now + lifetime, "jti": secrets.token_hex(16)}
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)


def _decode(token: str, expected_type: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key.get_secret_value(), algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from error
    if payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    return payload


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token_pair(db: Session, user: User) -> dict:
    settings = get_settings()
    access = _encode(
        {"sub": str(user.id), "type": "access"},
        timedelta(minutes=settings.access_token_minutes),
    )
    refresh = _encode(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=settings.refresh_token_days),
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_token_hash(refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",  # nosec B105 - OAuth2 token type label, not a secret
        "expires_in": settings.access_token_minutes * 60,
    }


def rotate_refresh_token(db: Session, refresh_token: str) -> dict:
    """Exchange a refresh token for a new pair; detect and punish reuse."""
    payload = _decode(refresh_token, "refresh")
    user_id = int(payload["sub"])
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == _token_hash(refresh_token))
    )
    if record is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown refresh token")
    now = datetime.now(UTC)
    expires = record.expires_at
    if expires.tzinfo is None:  # SQLite returns naive datetimes
        expires = expires.replace(tzinfo=UTC)
    if record.revoked_at is not None:
        # Rotation reuse — likely theft. Revoke the whole family for this user.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        logger.warning("refresh_token_reuse_detected user_id=%s", user_id)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token reuse detected")
    if expires < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")
    record.revoked_at = now
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return issue_token_pair(db, user)


def revoke_all_tokens(db: Session, user_id: int) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.commit()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = _decode(header.removeprefix("Bearer "), "access")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    if not request.headers.get("Authorization", "").startswith("Bearer "):
        return None
    return get_current_user(request, db)
