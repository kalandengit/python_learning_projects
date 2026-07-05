"""Application configuration.

Settings are read from the environment (see ``.env`` in production). Defaults
are chosen so the app boots for local development and tests without extra setup.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STAFFHUB_", env_file=".env", extra="ignore")

    # Core
    app_name: str = "StaffHub"
    environment: str = "development"
    debug: bool = True

    # Database. SQLite by default so the project runs and tests without a server;
    # production uses PostgreSQL (with row-level security) via this same URL.
    database_url: str = "sqlite:///./staffhub.db"

    # Auth / JWT
    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    invite_token_ttl_hours: int = 72
    reset_token_ttl_hours: int = 24

    # ICS calendar feed
    ics_token_ttl_days: int = 365

    # Rate limiting (requests per window per tenant+identity)
    rate_limit_login: int = 10
    rate_limit_uploads: int = 20
    rate_limit_requests: int = 60
    rate_limit_ics: int = 30
    rate_limit_window_seconds: int = 60

    # Attachments
    max_attachment_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_attachment_types: tuple[str, ...] = ("image/jpeg", "image/png", "application/pdf")

    # Soft-delete retention before hard purge
    soft_delete_retention_days: int = 90


@lru_cache
def get_settings() -> Settings:
    return Settings()
