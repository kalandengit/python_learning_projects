"""Declarative base and reusable model mixins."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime | None) -> datetime | None:
    """Coerce a datetime to UTC-aware.

    SQLite does not persist tzinfo, so datetimes read back are naive; PostgreSQL
    returns aware values. Normalising here lets comparisons work on both."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class SoftDeleteMixin:
    """Soft delete with retention. Rows are hidden by filtering ``deleted_at``;
    a scheduled purge job removes them after the retention window."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class TenantMixin:
    """Every tenant-scoped row carries ``tenant_id``. In production PostgreSQL,
    row-level security enforces this; the service layer mirrors it for SQLite
    and defence in depth."""

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
