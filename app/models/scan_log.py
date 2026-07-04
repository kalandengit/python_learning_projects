"""Scan logs — every scan recorded, accepted AND rejected (evacuation tracking, NIS2 audit)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ScanResult, ScanSubject, UUIDPkMixin


class ScanLog(UUIDPkMixin, Base):
    """Append-only — UPDATE/DELETE forbidden by a DB trigger (baseline migration)."""

    __tablename__ = "scan_logs"

    subject_type: Mapped[ScanSubject] = mapped_column(
        Enum(ScanSubject, name="scan_subject", values_callable=lambda e: [m.value for m in e])
    )
    subject_id: Mapped[uuid.UUID | None]  # NULL when the QR payload was unparseable
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"))
    result: Mapped[ScanResult] = mapped_column(
        Enum(ScanResult, name="scan_result", values_callable=lambda e: [m.value for m in e])
    )
    reason: Mapped[str | None] = mapped_column(Text)
    zone: Mapped[str | None] = mapped_column(String(120))
    device_id: Mapped[str] = mapped_column(String(120))
    scanned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    scanned_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (Index("ix_scan_logs_event_time", "event_id", "scanned_at"),)
