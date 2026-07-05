"""Request attachments with malware-scan gating and HR-only medical docs."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"


class Attachment(UUIDMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "attachments"

    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("requests.id"), index=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(String(400), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)

    scan_status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.PENDING)
    # Medical documents are encrypted at rest and restricted to HR.
    is_medical: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def is_available(self) -> bool:
        """Downloadable only once a scan confirms it is clean."""
        return self.scan_status == ScanStatus.CLEAN and not self.is_deleted
