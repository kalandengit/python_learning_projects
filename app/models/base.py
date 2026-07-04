"""Declarative base, naming conventions and shared mixins."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {datetime: DateTime(timezone=True)}  # noqa: RUF012


class UUIDPkMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class UserRole(enum.StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    EVENT_ORGANIZER = "EVENT_ORGANIZER"
    BOX_OFFICE_STAFF = "BOX_OFFICE_STAFF"
    SECURITY_GUARD = "SECURITY_GUARD"
    ATTENDEE = "ATTENDEE"


class TicketStatus(enum.StrEnum):
    CREATED = "created"
    VALID = "valid"
    USED = "used"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class BadgeType(enum.StrEnum):
    MANAGEMENT_TEAM = "MANAGEMENT_TEAM"
    SECURITY_STAFF = "SECURITY_STAFF"
    CONTRACTORS = "CONTRACTORS"
    VIP_VISITORS = "VIP_VISITORS"
    STANDARD_ATTENDEE = "STANDARD_ATTENDEE"


class ScanSubject(enum.StrEnum):
    TICKET = "ticket"
    BADGE = "badge"


class ScanResult(enum.StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


# Scanner roles allowed to call the validate endpoints (rate-limited per device).
SCANNER_ROLES = frozenset(
    {UserRole.SUPER_ADMIN, UserRole.BOX_OFFICE_STAFF, UserRole.SECURITY_GUARD}
)
