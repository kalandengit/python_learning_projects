"""Application settings, loaded from environment / .env, plus logging setup."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

Domain = Literal["law", "nko", "islamic", "cs", "general"]
DOMAINS: tuple[Domain, ...] = ("law", "nko", "islamic", "cs", "general")

DOMAIN_LABELS: dict[str, dict[str, str]] = {
    "law": {"en": "Law & Courts", "fr": "Droit & Tribunaux"},
    "nko": {"en": "N'Ko Writing", "fr": "Écriture N'Ko"},
    "islamic": {"en": "Islamic Sciences", "fr": "Sciences islamiques"},
    "cs": {"en": "Computer Science", "fr": "Informatique"},
    "general": {"en": "General", "fr": "Général"},
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    mistral_api_key: str = ""
    web_password: str = "change-me-please"

    telegram_bot_token: str = ""
    telegram_allowed_user_id: str = ""

    chat_model: str = "mistral-large-latest"
    embed_model: str = "mistral-embed"
    ocr_model: str = "mistral-ocr-latest"
    transcribe_model: str = "voxtral-mini-latest"

    # Empty -> embedded Qdrant stored under data/qdrant (no Docker needed locally).
    qdrant_url: str = ""
    qdrant_collection: str = "knowledge"

    uploads_dir: Path = BASE_DIR / "uploads"
    data_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    finetune_dir: Path = BASE_DIR / "finetune_data"

    chunk_chars: int = 1800  # ~450-512 tokens
    chunk_overlap_chars: int = 270  # ~15%
    retrieve_candidates: int = 20
    context_chunks: int = 6

    # Scaling / edge-case guards (see docs/en/10-limits.md)
    max_upload_mb: int = 500  # web upload cap, streamed to disk
    max_ocr_mb: int = 45  # Mistral OCR file-size limit safety margin
    audio_segment_minutes: int = 100  # longer recordings are split automatically
    embed_batch_char_budget: int = 40_000  # max characters per embeddings request
    chat_rate_per_min: int = 30  # protects your API budget if the password leaks

    def require_api_key(self) -> str:
        if not self.mistral_api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. Copy .env.example to .env and add your key "
                "(see docs/en/01-setup.md / docs/fr/01-setup.md)."
            )
        return self.mistral_api_key


settings = Settings()


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure console + file logging once; return the app logger."""
    logger = logging.getLogger("expert_consortium")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.logs_dir / "app.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger
