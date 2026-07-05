"""Tenant-aware, fixed-window rate limiter.

An in-memory implementation is used by default so the app and tests run without
Redis. Production swaps in a Redis-backed counter with the same interface; the
window/limit semantics are identical.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _Window:
    count: int = 0
    reset_at: float = 0.0


@dataclass
class RateLimiter:
    window_seconds: int
    _buckets: dict[str, _Window] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def hit(self, key: str, limit: int) -> bool:
        """Register one request for ``key``. Return True if allowed, False if the
        limit for the current window is exceeded."""
        now = time.monotonic()
        with self._lock:
            window = self._buckets.get(key)
            if window is None or now >= window.reset_at:
                window = _Window(count=0, reset_at=now + self.window_seconds)
                self._buckets[key] = window
            window.count += 1
            return window.count <= limit

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()
