"""Events (PostGIS point + geofence) and ticket tiers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.org import Organization


class Event(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    venue_name: Mapped[str | None] = mapped_column(String(300))
    # WGS84 point; GIST index created in the baseline migration.
    location: Mapped[Any | None] = mapped_column(Geometry(geometry_type="POINT", srid=4326))
    geofence_radius_m: Mapped[int | None]
    is_published: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)  # optimistic concurrency

    organization: Mapped[Organization] = relationship(back_populates="events")
    tiers: Mapped[list[TicketTier]] = relationship(back_populates="event")

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="window"),
        Index("ix_events_org_starts", "organization_id", "starts_at"),
        Index("ix_events_published_created", "is_published", "created_at", "id"),
    )


class TicketTier(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "ticket_tiers"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    price_cents: Mapped[int]  # 0 = FREE
    currency: Mapped[str] = mapped_column(String(3), default="eur")
    capacity: Mapped[int]
    # Guarded by SELECT … FOR UPDATE in ticket_service — zero overselling (§2, non-negotiable).
    sold_count: Mapped[int] = mapped_column(default=0)
    sales_starts_at: Mapped[datetime | None]
    sales_ends_at: Mapped[datetime | None]

    event: Mapped[Event] = relationship(back_populates="tiers")

    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="price_nonneg"),
        CheckConstraint("capacity >= 0", name="capacity_nonneg"),
        CheckConstraint("sold_count >= 0 AND sold_count <= capacity", name="no_oversell"),
    )
