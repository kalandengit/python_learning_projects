"""Organizations, users and WebAuthn credentials."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UserRole, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.event import Event


class Organization(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), unique=True)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    events: Mapped[list[Event]] = relationship(back_populates="organization")


class User(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), unique=True)  # stored lowercased
    full_name: Mapped[str | None] = mapped_column(String(200))
    # Argon2id (or legacy bcrypt, transparently rehashed on login). NULL = passkey-only account.
    password_hash: Mapped[str | None] = mapped_column(String(300))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e])
    )
    # TOTP secret encrypted at rest (AES-GCM, key from Secrets Manager) — never logged.
    totp_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    # GDPR
    marketing_consent: Mapped[bool] = mapped_column(default=False)
    terms_accepted_at: Mapped[datetime | None]
    anonymized_at: Mapped[datetime | None]

    organization: Mapped[Organization] = relationship(back_populates="users")
    webauthn_credentials: Mapped[list[WebAuthnCredential]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_users_email_lower", func.lower(email), unique=True),)


class WebAuthnCredential(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "webauthn_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary)
    sign_count: Mapped[int] = mapped_column(default=0)  # clone detection
    transports: Mapped[list[str] | None] = mapped_column(JSONB)
    aaguid: Mapped[str | None] = mapped_column(String(64))
    last_used_at: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="webauthn_credentials")
