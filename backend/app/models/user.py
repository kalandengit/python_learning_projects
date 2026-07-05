"""User accounts and invitation/reset tokens."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    PLANNER = "planner"
    HR = "hr"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"


class User(UUIDMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.EMPLOYEE)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.INVITED)

    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Forces a password change on next login (e.g. admin-triggered reset).
    must_reset_password: Mapped[bool] = mapped_column(Boolean, default=False)
    # MFA-ready: secret is populated when a user enrols; None means MFA off.
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthTokenKind(str, enum.Enum):
    INVITE = "invite"
    RESET = "reset"


class AuthToken(UUIDMixin, TimestampMixin, Base):
    """Single-use invitation / password-reset token. The raw value is emailed;
    only its hash is stored."""

    __tablename__ = "auth_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    kind: Mapped[AuthTokenKind] = mapped_column(Enum(AuthTokenKind), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")
