"""Application settings.

Every value comes from the environment (prefix ``NKO_``) or ``.env``.
Secrets are ``SecretStr`` so they never leak into logs or reprs.
"""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NKO_", env_file=".env", extra="ignore")

    secret_key: SecretStr
    database_url: str = "sqlite:///./nko.db"

    access_token_minutes: int = 15
    refresh_token_days: int = 7

    # ASR
    asr_engine: str = "mock"  # engine used for Manding languages: mock | mms | whisper
    mms_model_id: str = "facebook/mms-1b-all"
    mms_revision: str = "main"  # pin to a commit hash in production
    mms_model_dir: str | None = None
    mms_local_files_only: bool = False
    whisper_model: str = "openai/whisper-large-v3"
    mistral_api_key: SecretStr | None = None
    mistral_api_base: str = "https://api.mistral.ai"
    mistral_transcribe_model: str = "voxtral-mini-latest"

    # Limits & security
    max_upload_bytes: int = 10 * 1024 * 1024
    trusted_proxies: list[str] = []
    rate_limit_default: str = "120/minute"
    rate_limit_auth: str = "10/minute"
    rate_limit_transcribe: str = "20/minute"
    internal_health_token: SecretStr | None = None

    @field_validator("secret_key")
    @classmethod
    def _secret_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("NKO_SECRET_KEY must be at least 32 characters")
        return value

    @field_validator("asr_engine")
    @classmethod
    def _known_engine(cls, value: str) -> str:
        if value not in {"mock", "mms", "whisper"}:
            raise ValueError("NKO_ASR_ENGINE must be 'mock', 'mms', or 'whisper'")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
