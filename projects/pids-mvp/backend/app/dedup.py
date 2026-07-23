"""Event deduplication.

The ingestion pipeline is assumed to be *at-least-once* (Kafka default), so consumers must be
idempotent. We derive a stable ``idempotency_key`` per logical detection and drop repeats that
fall inside a configurable time window (master prompt §8).

The in-memory backend is fine for a single process / the MVP; for a horizontally-scaled
deployment inject the Redis backend so the dedup set is shared across workers.
"""
from __future__ import annotations

import hashlib
import time
from typing import Protocol


def compute_idempotency_key(
    *, camera_id: str, object_class: str, ts_epoch: float, window_seconds: int, track_id: str | None = None
) -> str:
    """Stable key for a logical detection.

    Detections from the same camera/class (and track, if provided) landing in the same time
    bucket collapse to one key — so retries and rapid duplicate frames dedup, but a genuinely
    new detection in the next bucket does not.
    """
    bucket = int(ts_epoch // max(window_seconds, 1))
    raw = f"{camera_id}|{object_class}|{track_id or '-'}|{bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class DedupBackend(Protocol):
    def seen(self, key: str, ttl_seconds: int) -> bool:  # pragma: no cover - interface
        """Return True if key was already recorded; otherwise record it and return False."""


class InMemoryDedup:
    """Process-local dedup with lazy TTL expiry. Not shared across processes.

    Expiry is swept on a throttled cadence (``purge_interval``) rather than on every call, so
    ``seen()`` stays amortized O(1) even when the store holds many live keys. A full O(n) sweep
    runs at most once per interval.
    """

    def __init__(self, purge_interval: float = 1.0) -> None:
        self._store: dict[str, float] = {}
        self._purge_interval = purge_interval
        self._next_purge = 0.0

    def _maybe_purge(self, now: float) -> None:
        if now < self._next_purge:
            return
        self._next_purge = now + self._purge_interval
        expired = [k for k, exp in self._store.items() if exp <= now]
        for k in expired:
            del self._store[k]

    def seen(self, key: str, ttl_seconds: int) -> bool:
        now = time.time()
        self._maybe_purge(now)
        exp = self._store.get(key)
        if exp is not None and exp > now:
            return True
        self._store[key] = now + ttl_seconds
        return False


class RedisDedup:  # pragma: no cover - requires a live Redis
    """Distributed dedup using Redis SET NX with expiry. Shared across workers."""

    def __init__(self, client) -> None:
        self._r = client

    def seen(self, key: str, ttl_seconds: int) -> bool:
        # SET key 1 NX EX ttl -> returns True if set (i.e. not seen), None if it existed.
        was_set = self._r.set(f"dedup:{key}", "1", nx=True, ex=ttl_seconds)
        return not bool(was_set)
