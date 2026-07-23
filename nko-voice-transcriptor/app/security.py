"""Authentication and password handling.

* Passwords: Argon2id (argon2-cffi defaults — memory-hard, current OWASP
  recommendation).
* Sessions: short-lived HS256 JWT access tokens carrying only the user id.
"""

from __future__ import annotations

import contextlib
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

# Precomputed Argon2 hash of a throwaway value. Verifying against it for a
# non-existent user makes the failure path spend the same work as a real
# wrong-password check, so login timing does not reveal whether a username
# exists (defence against user enumeration via response time).
_DUMMY_HASH = _hasher.hash("nko-timing-uniform-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def verify_dummy(password: str) -> None:
    """Spend one Argon2 verification to equalize timing for absent users."""
    with contextlib.suppress(Exception):
        _hasher.verify(_DUMMY_HASH, password)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def new_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    return token, hashlib.sha256(token.encode()).hexdigest()


def refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    from app.models import User

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise unauthorized from None
    if payload.get("type") != "access":
        raise unauthorized
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
