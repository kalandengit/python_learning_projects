"""StaffHub FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .database import engine
from .models import Base
from .routers import (
    admin,
    attachments,
    auth,
    ics,
    notifications,
    planning,
    requests,
    timeline,
)

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        version="0.1.0",
        description="Employee self-service & shift planning portal (MVP backend).",
    )

    # For SQLite/dev the schema is created on startup. Production uses Alembic
    # migrations against PostgreSQL instead of create_all.
    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(planning.router)
    app.include_router(requests.router)
    app.include_router(attachments.router)
    app.include_router(notifications.router)
    app.include_router(timeline.router)
    app.include_router(ics.router)
    app.include_router(admin.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "env": settings.environment}

    return app


app = create_app()
