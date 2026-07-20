"""Application configuration.

All runtime configuration comes from environment variables (or a local `.env`
file in development). Secrets must never be committed — in deployed
environments they are injected from the platform secrets manager.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASA_",
        extra="ignore",
    )

    environment: Literal["dev", "test", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    # Infrastructure endpoints (consumed from Milestone 1 onward).
    database_url: str = "postgresql+asyncpg://asa:asa@localhost:5432/asa"
    redis_url: str = "redis://localhost:6379/0"
    object_store_endpoint: str = "http://localhost:9000"

    # CORS origins for the web frontend.
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
