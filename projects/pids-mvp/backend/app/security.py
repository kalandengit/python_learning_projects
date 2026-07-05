"""Authentication & authorization.

Password hashing uses PBKDF2-HMAC-SHA256 (stdlib) and tokens are HS256-signed (stdlib hmac).
This keeps the MVP dependency-light and fully runnable. **For production**, prefer argon2/bcrypt
for password hashing and a vetted JWT library (PyJWT) with asymmetric keys, and integrate an
OIDC provider (see master prompt §Paramètres / §22).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

_PBKDF2_ROUNDS = 200_000

# Role hierarchy — higher number grants everything below it.
ROLE_LEVELS = {"viewer": 10, "technician": 20, "operator": 30, "admin": 40, "super_admin": 50}


# --------------------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${_PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_hex, hash_hex = stored.split("$")
        assert algo == "pbkdf2_sha256"
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AssertionError):
        return False


# --------------------------------------------------------------------------- tokens (HS256)
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(subject: str, role: str, tenant_id: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(time.time()) + settings.access_token_ttl_seconds,
    }
    signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(payload).encode())}"
    sig = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(sig)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64d(sig_b64)):
            raise ValueError("bad signature")
        payload = json.loads(_b64d(payload_b64))
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("expired")
        return payload
    except (ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token") from exc


# --------------------------------------------------------------------------- dependencies
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    user = db.get(User, payload["sub"])
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found or inactive")
    return user


def require_role(minimum: str):
    """Dependency factory enforcing a minimum role (RBAC)."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVELS.get(user.role, 0) < ROLE_LEVELS.get(minimum, 999):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires role >= {minimum}")
        return user

    return _dep
