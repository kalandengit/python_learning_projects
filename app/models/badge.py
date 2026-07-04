"""Role-based badges with zone ABAC (JSONB zones)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BadgeType, TimestampMixin, UUIDPkMixin


class Badge(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "badges"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    holder_name: Mapped[str] = mapped_column(String(200))
    type: Mapped[BadgeType] = mapped_column(
        Enum(BadgeType, name="badge_type", values_callable=lambda e: [m.value for m in e])
    )
    # Zone ABAC: list of zone slugs; MANAGEMENT_TEAM bypasses the check (all-access).
    access_zones: Mapped[list[str]] = mapped_column(JSONB, default=list)
    nfc_uid: Mapped[str | None] = mapped_column(String(64), unique=True)
    valid_from: Mapped[datetime]
    valid_until: Mapped[datetime]
    is_active: Mapped[bool] = mapped_column(default=True)  # instant toggle
    qr_token: Mapped[str] = mapped_column(String(64), unique=True)
    pqc_signature: Mapped[bytes | None] = mapped_column(LargeBinary)
