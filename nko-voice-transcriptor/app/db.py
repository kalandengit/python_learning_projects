"""Database engine and session management (SQLAlchemy 2.x).

SQLite for development, PostgreSQL in production via ``NKO_DATABASE_URL``.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # In-memory SQLite: one shared connection, else every pooled
            # connection would see its own empty database.
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = None
SessionLocal: sessionmaker | None = None


def init_db() -> None:
    """Create engine + tables. Called at app startup (and by tests)."""
    global engine, SessionLocal
    if engine is None:
        engine = _make_engine()
        SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    # Import models so metadata is populated before create_all
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    assert SessionLocal is not None, "init_db() must run at startup"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
