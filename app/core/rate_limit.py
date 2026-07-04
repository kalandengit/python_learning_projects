"""Valkey sliding-window-log rate limiter (§2).

100 scans/min/device · 30 purchases/hr/user · auth endpoints per-IP.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from valkey.asyncio import Valkey


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after_seconds: int


class RateLimiter:
    def __init__(self, client: Valkey) -> None:
        self._v = client

    async def hit(self, bucket: str, *, limit: int, window_seconds: int) -> RateDecision:
        now = time.time()
        key = f"rl:{bucket}"
        member = f"{now:.6f}:{uuid.uuid4().hex[:8]}"
        async with self._v.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {member: now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds + 1)
            _, _, count, _ = await pipe.execute()
        if int(count) <= limit:
            return RateDecision(allowed=True, retry_after_seconds=0)
        oldest = await self._v.zrange(key, 0, 0, withscores=True)
        retry = int(oldest[0][1] + window_seconds - now) + 1 if oldest else window_seconds
        return RateDecision(allowed=False, retry_after_seconds=max(retry, 1))
