"""Application settings — env-driven, secrets never logged (SecretStr)."""

from __future__ import annotations

import base64
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMS_", env_file=".env", extra="ignore")

    env: Literal["dev", "test", "staging", "prod"] = "dev"
    api_v1_prefix: str = "/api/v1"

    # PostgreSQL 18 + PostGIS 3.6 (asyncpg driver)
    database_url: str = "postgresql+asyncpg://ems:ems@localhost:5432/ems"
    db_pool_size: int = 10
    db_max_overflow: int = 10

    # Valkey 8 (redis-protocol URL accepted by the valkey client)
    valkey_url: str = "redis://localhost:6379/0"

    # --- JWT (PyJWT, RS256) -------------------------------------------------
    jwt_private_key_pem: SecretStr | None = None
    jwt_public_key_pem: str | None = None
    access_token_ttl_seconds: int = 900  # 15 min
    refresh_token_ttl_seconds: int = 7 * 24 * 3600  # 7 d, rotation + reuse detection
    mfa_token_ttl_seconds: int = 300

    # --- Account lockout (Valkey) --------------------------------------------
    lockout_max_failures: int = 5
    lockout_duration_seconds: int = 900  # 15 min

    # --- QR / PQC -------------------------------------------------------------
    qr_hmac_secret: SecretStr | None = None
    qr_max_age_seconds: int = 90  # client refreshes ≤60 s; +30 s clock skew
    pqc_algorithm: str = "ML-DSA-65"  # FIPS 204; legacy names mapped via ALGORITHM_ALIASES
    pqc_secret_key_b64: SecretStr | None = None
    pqc_public_key_b64: str | None = None
    # HMAC-only fallback is for dev/test without liboqs — refused in staging/prod.
    pqc_allow_hmac_only: bool = False

    # --- TOTP secret encryption at rest (AES-256-GCM key, base64, 32 bytes) ---
    totp_enc_key_b64: SecretStr | None = None

    # --- Stripe (Checkout Sessions; card data never touches the server) -------
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None

    # --- WebAuthn / passkeys ---------------------------------------------------
    rp_id: str = "localhost"
    rp_name: str = "EMS"
    rp_origin: str = "http://localhost:5173"
    webauthn_challenge_ttl_seconds: int = 300

    # --- Rate limits (Valkey sliding-window log) -------------------------------
    scan_rate_per_device_per_minute: int = 100
    purchase_rate_per_user_per_hour: int = 30
    auth_rate_per_ip_per_minute: int = 10

    # --- Frontend / redirects ---------------------------------------------------
    frontend_base_url: str = "http://localhost:5173"

    # --- Observability -----------------------------------------------------------
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "ems-api"

    @field_validator("database_url")
    @classmethod
    def _force_asyncpg(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_dev_like(self) -> bool:
        return self.env in ("dev", "test")

    def totp_enc_key(self) -> bytes:
        if self.totp_enc_key_b64 is None:
            raise RuntimeError("EMS_TOTP_ENC_KEY_B64 is not configured")
        key = base64.b64decode(self.totp_enc_key_b64.get_secret_value())
        if len(key) != 32:
            raise RuntimeError("TOTP encryption key must be 32 bytes (AES-256-GCM)")
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()
