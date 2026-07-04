"""Liveness/readiness: verifies DB and Valkey connectivity."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from valkey.asyncio import Valkey

from app.core.deps import get_valkey
from app.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    valkey: Annotated[Valkey, Depends(get_valkey)],
) -> dict[str, str]:
    checks = {"database": "ok", "valkey": "ok"}
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "down"
    try:
        await valkey.ping()
    except Exception:
        checks["valkey"] = "down"
    if "down" in checks.values():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", **checks}
    return {"status": "ok", **checks}
