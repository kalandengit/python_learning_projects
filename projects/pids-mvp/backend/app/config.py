"""Application configuration.

Values are read from environment variables (12-factor). See ``.env.example``.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIDS_", env_file=".env", extra="ignore")

    # Database — SQLite by default so the MVP runs with zero infra.
    # In production point this at PostgreSQL, e.g.
    #   postgresql+psycopg://user:pass@host:5432/pids
    database_url: str = "sqlite:///./pids.db"

    # Auth. Override with a strong random value in production (secrets manager).
    secret_key: str = "dev-only-change-me"
    access_token_ttl_seconds: int = 3600

    # Deduplication window for incoming detection events (seconds).
    dedup_window_seconds: int = 30

    # Optional Redis URL for distributed dedup/cache. Falls back to in-memory.
    redis_url: str | None = None

    # Default confidence floor below which events are ignored outright.
    min_confidence: float = 0.4

    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
