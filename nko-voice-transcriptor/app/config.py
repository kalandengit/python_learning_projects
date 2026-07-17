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

    # Optional OpenAI-compatible text cleanup after speech recognition.
    # Credentials are server-side only and are never returned to the app.
    llm_provider: Literal["none", "openai", "groq", "custom"] = "none"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_timeout_seconds: int = 20

    # Comma-separated ISO 639-3 codes offered as source languages. Each must
    # be a Manding language covered by both MMS and the N'Ko transliterator.
    languages: str = "bam,dyu,emk,mku,msc,mwk"
    default_language: str = "bam"

    max_upload_bytes: int = 10 * 1024 * 1024
    max_audio_seconds: int = 120
    segment_seconds: int = 20
    silence_threshold_db: int = -40
    training_data_dir: str = "./training-data"
    review_api_key: str = ""
    correction_memory_enabled: bool = True
    mms_adapter_path: str = ""
    model_version: str = "base"

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

    @model_validator(mode="after")
    def llm_configuration_valid(self) -> Settings:
        if self.llm_provider != "none" and not self.llm_api_key:
            raise ValueError("NKO_LLM_API_KEY is required when NKO_LLM_PROVIDER is enabled")
        if self.llm_provider == "custom" and not self.llm_base_url:
            raise ValueError("NKO_LLM_BASE_URL is required for the custom provider")
        if self.llm_base_url and not self.llm_base_url.startswith(("https://", "http://")):
            raise ValueError("NKO_LLM_BASE_URL must use HTTPS or HTTP")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
