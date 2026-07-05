"""Per-user ICS calendar feed tokens (hashed, self-service revoke, annual expiry)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin


class IcsToken(UUIDMixin, TenantMixin, TimestampMixin, Base):
    """The feed URL embeds a UUIDv4 token; only its hash is stored so a leaked
    database cannot be used to derive live feed URLs."""

    __tablename__ = "ics_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
