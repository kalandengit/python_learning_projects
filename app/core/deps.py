"""FastAPI dependencies: app-state accessors, auth (JWT → AuthContext),
RBAC guards and rate-limit gates. All auth failures are generic 401/403 —
no enumeration, no token internals (§4 invariants).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from valkey.asyncio import Valkey

from app.config import Settings
from app.core.pqc import HybridSigner
from app.core.rate_limit import RateLimiter
from app.core.security import AuthContext, SessionStore, TokenError, TokenIssuer
from app.models import SCANNER_ROLES, UserRole
from app.services.qr_service import QRService
from app.services.stripe_service import StripeService

_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required",
    headers={"WWW-Authenticate": "Bearer"},
)
_FORBIDDEN = HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_valkey(request: Request) -> Valkey:
    client: Valkey = request.app.state.valkey
    return client


def get_token_issuer(request: Request) -> TokenIssuer:
    issuer: TokenIssuer = request.app.state.token_issuer
    return issuer


def get_session_store(request: Request) -> SessionStore:
    store: SessionStore = request.app.state.session_store
    return store


def get_qr_service(request: Request) -> QRService:
    service: QRService = request.app.state.qr_service
    return service


def get_signer(request: Request) -> HybridSigner:
    signer: HybridSigner = request.app.state.pqc_signer
    return signer


def get_stripe(request: Request) -> StripeService:
    service: StripeService = request.app.state.stripe
    return service


def get_rate_limiter(request: Request) -> RateLimiter:
    limiter: RateLimiter = request.app.state.rate_limiter
    return limiter


async def get_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
) -> AuthContext:
    if credentials is None:
        raise _UNAUTHORIZED
    try:
        claims = issuer.decode(credentials.credentials, "access")
        return issuer.auth_context(claims)
    except TokenError as exc:
        raise _UNAUTHORIZED from exc


def require_roles(*roles: UserRole) -> Callable[..., Awaitable[AuthContext]]:
    allowed = frozenset(roles)

    async def guard(auth: Annotated[AuthContext, Depends(get_auth)]) -> AuthContext:
        if auth.role not in allowed:
            raise _FORBIDDEN
        return auth

    return guard


require_scanner = require_roles(*SCANNER_ROLES)
require_organizer = require_roles(UserRole.SUPER_ADMIN, UserRole.EVENT_ORGANIZER)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_ip(scope: str) -> Callable[..., Awaitable[None]]:
    """Per-IP sliding-window gate for auth endpoints (§2)."""

    async def gate(
        request: Request,
        limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
        settings: Annotated[Settings, Depends(get_app_settings)],
    ) -> None:
        decision = await limiter.hit(
            f"{scope}:ip:{client_ip(request)}",
            limit=settings.auth_rate_per_ip_per_minute,
            window_seconds=60,
        )
        if not decision.allowed:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )

    return gate
