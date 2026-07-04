"""Tickets and their append-only status history."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TicketStatus, TimestampMixin, UUIDPkMixin

_status_enum = Enum(
    TicketStatus, name="ticket_status", values_callable=lambda e: [m.value for m in e]
)


class Ticket(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    tier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ticket_tiers.id", ondelete="RESTRICT"), index=True
    )
    # Denormalised for scan-path speed (<200 ms SLO) — set once at purchase.
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[TicketStatus] = mapped_column(_status_enum, default=TicketStatus.CREATED)
    # Opaque random token carried in the QR envelope — never contains PII.
    qr_token: Mapped[str] = mapped_column(String(64), unique=True)
    # Hybrid ML-DSA-65 + HMAC signature over the static QR payload {t,e,u},
    # generated at issuance and re-verified on every scan.
    pqc_signature: Mapped[bytes | None] = mapped_column(LargeBinary)
    used_at: Mapped[datetime | None]

    history: Mapped[list[TicketStatusHistory]] = relationship(back_populates="ticket")

    __table_args__ = (Index("ix_tickets_owner_created", "owner_id", "created_at", "id"),)


class TicketStatusHistory(UUIDPkMixin, Base):
    """Append-only audit trail — UPDATE/DELETE forbidden by a DB trigger (baseline migration)."""

    __tablename__ = "ticket_status_history"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="RESTRICT"), index=True
    )
    from_status: Mapped[TicketStatus | None] = mapped_column(_status_enum)
    to_status: Mapped[TicketStatus] = mapped_column(_status_enum)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ticket: Mapped[Ticket] = relationship(back_populates="history")
