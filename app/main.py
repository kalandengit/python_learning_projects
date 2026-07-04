"""EMS API application factory.

Generic error responses only (no stack traces, no enumeration); all shared
resources (engine, Valkey, keys, signer, services) live on app.state and are
created/torn down by the lifespan context.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from valkey.asyncio import Valkey

from app.config import Settings, get_settings
from app.core.keys import get_key_material
from app.core.pqc import get_hybrid_signer
from app.core.rate_limit import RateLimiter
from app.core.security import SessionStore, TokenIssuer
from app.db import build_engine, build_sessionmaker
from app.routers import auth, badges, events, health, passkeys, tickets, users, webhooks
from app.services.qr_service import QRService
from app.services.stripe_service import StripeService
from app.telemetry import setup_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    keys = get_key_material(settings)

    engine = build_engine(settings)
    app.state.engine = engine
    app.state.sessionmaker = build_sessionmaker(engine)
    app.state.valkey = Valkey.from_url(settings.valkey_url, decode_responses=True)

    app.state.token_issuer = TokenIssuer(
        keys.jwt_private_pem,
        keys.jwt_public_pem,
        access_ttl=settings.access_token_ttl_seconds,
        refresh_ttl=settings.refresh_token_ttl_seconds,
        mfa_ttl=settings.mfa_token_ttl_seconds,
    )
    app.state.session_store = SessionStore(
        app.state.valkey,
        refresh_ttl=settings.refresh_token_ttl_seconds,
        lockout_max=settings.lockout_max_failures,
        lockout_ttl=settings.lockout_duration_seconds,
    )
    app.state.qr_service = QRService(
        keys.qr_hmac_secret, max_age_seconds=settings.qr_max_age_seconds
    )
    app.state.pqc_signer = get_hybrid_signer(settings, keys.qr_hmac_secret)
    app.state.stripe = StripeService.from_settings(settings)
    app.state.rate_limiter = RateLimiter(app.state.valkey)

    setup_telemetry(app, settings, engine)
    logger.info("EMS API started (env=%s)", settings.env)
    try:
        yield
    finally:
        await app.state.valkey.aclose()
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="EMS API",
        version="3.0.0",
        lifespan=_lifespan,
        # Interactive docs only in dev/test; the OpenAPI schema is still
        # generated for tooling but not served publicly in prod.
        docs_url="/docs" if settings.is_dev_like else None,
        redoc_url=None,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_base_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    prefix = settings.api_v1_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(passkeys.router, prefix=prefix)
    app.include_router(events.router, prefix=prefix)
    app.include_router(tickets.router, prefix=prefix)
    app.include_router(badges.router, prefix=prefix)
    app.include_router(webhooks.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(health.router)  # /health at the root (§4)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never expose stack traces or internals (§4 invariants).
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
