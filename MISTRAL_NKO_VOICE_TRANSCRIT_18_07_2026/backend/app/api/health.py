"""Liveness (public, minimal) and readiness (internal-only) endpoints."""

import hmac

from fastapi import APIRouter, HTTPException, Request, status

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    # Public liveness: no version, no engine details (audit finding).
    return {"status": "ok"}


@router.get("/health/detailed")
def health_detailed(request: Request):
    settings = get_settings()
    token = settings.internal_health_token
    provided = request.headers.get("X-Internal-Health", "")
    if token is None or not hmac.compare_digest(provided, token.get_secret_value()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
    return {
        "status": "ok",
        "version": __version__,
        "asr_engine": settings.asr_engine,
        "voxtral_configured": settings.mistral_api_key is not None,
    }
