"""Shared FastAPI dependencies: authentication, tenant context, rate limiting."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User, UserRole, UserStatus
from .security import decode_access_token
from .services.rate_limit import RateLimiter

settings = get_settings()

# Distinct limiters per protected surface (login, uploads, requests, ICS).
login_limiter = RateLimiter(settings.rate_limit_window_seconds)
upload_limiter = RateLimiter(settings.rate_limit_window_seconds)
request_limiter = RateLimiter(settings.rate_limit_window_seconds)
ics_limiter = RateLimiter(settings.rate_limit_window_seconds)


@dataclass
class CurrentUser:
    id: str
    tenant_id: str
    role: UserRole


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = decode_access_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.get(User, payload.get("sub"))
    if user is None or user.is_deleted or user.status != UserStatus.ACTIVE:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not active")
    # Token tenant must match the stored user's tenant (defence in depth).
    if user.tenant_id != payload.get("tenant_id"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tenant mismatch")

    return CurrentUser(id=user.id, tenant_id=user.tenant_id, role=user.role)


def require_roles(*roles: UserRole):
    """Dependency factory enforcing that the caller has one of ``roles``."""

    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _checker


def client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(limiter: RateLimiter, key: str, limit: int) -> None:
    if not limiter.hit(key, limit):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
