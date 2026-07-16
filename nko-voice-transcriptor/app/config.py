"""Application configuration.

All settings come from environment variables (prefix ``NKO_``) or a local
``.env`` file. The app fails fast at startup on invalid configuration rather
than misbehaving at request time.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NKO_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    secret_key: str
    database_url: str = "sqlite:///./nko.db"

    asr_engine: Literal["mock", "mms"] = "mock"
    mms_model_id: str = "facebook/mms-1b-all"

    # Comma-separated ISO 639-3 codes offered as source languages. Each must
    # be a Manding language covered by both MMS and the N'Ko transliterator.
    languages: str = "bam,dyu,emk,mku,msc,mwk"
    default_language: str = "bam"

    max_upload_bytes: int = 10 * 1024 * 1024
    max_audio_seconds: int = 120

    # Optional path to a full N'Ko–French lexicon JSON. Empty = bundled sample.
    lexicon_path: str = ""

    access_token_minutes: int = 60

    cors_origins: str = ""
    environment: Literal["development", "production"] = "development"

    @field_validator("secret_key")
    @classmethod
    def secret_key_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("NKO_SECRET_KEY must be at least 32 characters")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def language_list(self) -> list[str]:
        return [lang.strip() for lang in self.languages.split(",") if lang.strip()]

    @model_validator(mode="after")
    def default_language_supported(self) -> Settings:
        if self.default_language not in self.language_list:
            raise ValueError("NKO_DEFAULT_LANGUAGE must be one of NKO_LANGUAGES")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
