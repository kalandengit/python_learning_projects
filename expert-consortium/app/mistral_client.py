"""Shared Mistral API client with retry/backoff on transient errors."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, TypeVar

try:  # SDK >= 2.x
    from mistralai.client import Mistral
except ImportError:  # SDK 1.x
    from mistralai import Mistral
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

T = TypeVar("T")


@lru_cache(maxsize=1)
def get_client() -> Mistral:
    return Mistral(api_key=settings.require_api_key())


def _is_transient(exc: BaseException) -> bool:
    """Retry on rate limits (429), server errors (5xx), and network hiccups."""
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, (ConnectionError, TimeoutError))


@retry(
    retry=retry_if_exception(_is_transient),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def with_retry(fn: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Call ``fn(*args, **kwargs)``, retrying transient API failures with backoff."""
    return fn(*args, **kwargs)
