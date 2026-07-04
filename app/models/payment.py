"""Payments — Stripe references only; card data never touches the server (PCI SAQ-A)."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PaymentStatus, TimestampMixin, UUIDPkMixin


class Payment(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True
    )
    tier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ticket_tiers.id", ondelete="RESTRICT"))
    quantity: Mapped[int]
    amount_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3), default="eur")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=lambda e: [m.value for m in e]),
        default=PaymentStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255))
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_payments_user_idem"),)
