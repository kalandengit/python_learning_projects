"""Liveness endpoint."""

from fastapi import APIRouter, Request

from app import __version__
from app.config import get_settings
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthOut)
def health(request: Request):
    settings = get_settings()
    return HealthOut(
        status="ok",
        version=__version__,
        asr_engine=settings.asr_engine,
        model_version=settings.model_version,
    )
