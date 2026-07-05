"""Employee requests (desiderata / leave / absence) with a state machine
and full status history."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin


class RequestType(str, enum.Enum):
    DESIDERATA = "desiderata"
    LEAVE = "leave"
    ABSENCE = "absence"


class RequestState(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_INFORMATION = "needs_information"
    RESUBMITTED = "resubmitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# Allowed transitions per the master prompt:
#   Draft → Submitted → Under Review → Needs Information → Resubmitted →
#   Approved/Rejected/Cancelled
ALLOWED_TRANSITIONS: dict[RequestState, set[RequestState]] = {
    RequestState.DRAFT: {RequestState.SUBMITTED, RequestState.CANCELLED},
    RequestState.SUBMITTED: {RequestState.UNDER_REVIEW, RequestState.CANCELLED},
    RequestState.UNDER_REVIEW: {
        RequestState.NEEDS_INFORMATION,
        RequestState.APPROVED,
        RequestState.REJECTED,
        RequestState.CANCELLED,
    },
    RequestState.NEEDS_INFORMATION: {RequestState.RESUBMITTED, RequestState.CANCELLED},
    RequestState.RESUBMITTED: {
        RequestState.UNDER_REVIEW,
        RequestState.APPROVED,
        RequestState.REJECTED,
        RequestState.CANCELLED,
    },
    # Terminal states have no outgoing transitions.
    RequestState.APPROVED: set(),
    RequestState.REJECTED: set(),
    RequestState.CANCELLED: set(),
}

TERMINAL_STATES = {RequestState.APPROVED, RequestState.REJECTED, RequestState.CANCELLED}


class Request(UUIDMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "requests"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    type: Mapped[RequestType] = mapped_column(Enum(RequestType), nullable=False)
    state: Mapped[RequestState] = mapped_column(
        Enum(RequestState), default=RequestState.DRAFT, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    history: Mapped[list["RequestStatusHistory"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestStatusHistory.created_at",
    )


class RequestStatusHistory(UUIDMixin, TimestampMixin, Base):
    """One row per state transition, preserving who changed what and why."""

    __tablename__ = "request_status_history"

    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("requests.id"), index=True)
    from_state: Mapped[RequestState | None] = mapped_column(Enum(RequestState), nullable=True)
    to_state: Mapped[RequestState] = mapped_column(Enum(RequestState), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped[Request] = relationship(back_populates="history")
