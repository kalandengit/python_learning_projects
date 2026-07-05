"""Tenant and per-tenant feature flags."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Tenant(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    feature_flags: Mapped[list["FeatureFlag"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class FeatureFlag(UUIDMixin, TimestampMixin, Base):
    """A named capability toggled per tenant (e.g. ``background_sync``)."""

    __tablename__ = "feature_flags"
    __table_args__ = (UniqueConstraint("tenant_id", "key", name="uq_feature_flag_tenant_key"),)

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="feature_flags")
