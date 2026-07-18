"""Proxy-aware rate limiting (v1.2.0 audit finding).

``X-Forwarded-For`` is honored only when the direct peer is a configured
trusted proxy; otherwise the peer address keys the limiter, so clients
cannot spoof their way past limits.
"""

from fastapi import Request
from slowapi import Limiter

from app.config import get_settings


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    settings = get_settings()
    if peer in settings.trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return peer


limiter = Limiter(key_func=client_ip)


def auth_limit() -> str:
    return get_settings().rate_limit_auth


def transcribe_limit() -> str:
    return get_settings().rate_limit_transcribe


def default_limit() -> str:
    return get_settings().rate_limit_default
