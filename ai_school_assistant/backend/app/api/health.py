"""Liveness and readiness endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import APP_VERSION, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness probe: the process is up and serving requests."""
    settings = get_settings()
    return HealthResponse(status="ok", version=APP_VERSION, environment=settings.environment)


@router.get("/readyz", response_model=HealthResponse)
async def readyz() -> HealthResponse:
    """Readiness probe.

    From Milestone 1 this will verify database and Redis connectivity; at M0
    it mirrors liveness so orchestration wiring can be built and tested now.
    """
    settings = get_settings()
    return HealthResponse(status="ready", version=APP_VERSION, environment=settings.environment)
