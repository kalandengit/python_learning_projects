"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import ALL_ROUTERS
from .config import get_settings
from .database import SessionLocal, init_db
from .dedup import InMemoryDedup, RedisDedup
from .notifications import default_service
from .seed import seed

logging.basicConfig(level=logging.INFO)
settings = get_settings()


def _build_dedup():
    if settings.redis_url:
        try:  # pragma: no cover - optional dependency
            import redis  # type: ignore

            return RedisDedup(redis.from_url(settings.redis_url))
        except Exception:  # noqa: BLE001
            logging.warning("Redis unavailable; falling back to in-memory dedup")
    return InMemoryDedup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.dedup = _build_dedup()
    app.state.notifier = default_service()
    # Seed demo data on first boot (idempotent).
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="PIDS API",
    version="0.1.0",
    summary="Perimeter Intrusion Detection System — MVP core",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


for router in ALL_ROUTERS:
    app.include_router(router)
