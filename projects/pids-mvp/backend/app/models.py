"""SQLAlchemy ORM models — the PIDS domain.

UUIDs are stored as 32-char hex strings for portability across SQLite/PostgreSQL.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Many-to-many: a camera can belong to several zones.
camera_zone = Table(
    "camera_zone",
    Base.metadata,
    Column("camera_id", String(32), ForeignKey("camera.id"), primary_key=True),
    Column("zone_id", String(32), ForeignKey("zone.id"), primary_key=True),
)


class Tenant(Base):
    __tablename__ = "tenant"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    users = relationship("User", back_populates="tenant")
    sites = relationship("Site", back_populates="tenant")


class User(Base):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Roles: super_admin, admin, operator, technician, viewer
    role: Mapped[str] = mapped_column(String(20), default="operator")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tenant = relationship("Tenant", back_populates="users")


class Site(Base):
    __tablename__ = "site"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    name: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    tenant = relationship("Tenant", back_populates="sites")
    zones = relationship("Zone", back_populates="site")
    cameras = relationship("Camera", back_populates="site")


class Zone(Base):
    __tablename__ = "zone"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    site_id: Mapped[str] = mapped_column(String(32), ForeignKey("site.id"))
    name: Mapped[str] = mapped_column(String(120))
    # Detection geometry: {"type": "polygon"|"line", "points": [[x,y],...]}
    geometry: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    site = relationship("Site", back_populates="zones")
    cameras = relationship("Camera", secondary=camera_zone, back_populates="zones")


class Camera(Base):
    __tablename__ = "camera"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    site_id: Mapped[str] = mapped_column(String(32), ForeignKey("site.id"))
    name: Mapped[str] = mapped_column(String(120))
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    protocol: Mapped[str] = mapped_column(String(10), default="ONVIF")  # ONVIF|RTSP|VENDOR
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    orientation: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fov_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    firmware: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")  # online|offline|tamper|unknown
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    site = relationship("Site", back_populates="cameras")
    zones = relationship("Zone", secondary=camera_zone, back_populates="cameras")
    events = relationship("Event", back_populates="camera")


class Event(Base):
    __tablename__ = "event"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_event_idempotency"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    camera_id: Mapped[str] = mapped_column(String(32), ForeignKey("camera.id"))
    ts: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    object_class: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    track_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(80), index=True)

    camera = relationship("Camera", back_populates="events")
    alert = relationship("Alert", back_populates="event", uselist=False)


class Rule(Base):
    __tablename__ = "rule"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    name: Mapped[str] = mapped_column(String(120))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    # JSON Decision Model: list of {field, op, value}
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    # {"decision": "intrusion"|"false_positive"|"ignore", "criticality": "low|medium|high|critical"}
    action: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Alert(Base):
    __tablename__ = "alert"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenant.id"))
    event_id: Mapped[str] = mapped_column(String(32), ForeignKey("event.id"))
    camera_id: Mapped[str] = mapped_column(String(32), ForeignKey("camera.id"))
    zone_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("zone.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(40))
    criticality: Mapped[str] = mapped_column(String(20), default="medium")
    # NEW|IN_PROGRESS|ACKNOWLEDGED|CLOSED|FALSE_POSITIVE
    status: Mapped[str] = mapped_column(String(20), default="NEW")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)

    event = relationship("Event", back_populates="alert")
    history = relationship("AlertHistory", back_populates="alert", order_by="AlertHistory.at")
    notifications = relationship("Notification", back_populates="alert")


class AlertHistory(Base):
    __tablename__ = "alert_history"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    alert_id: Mapped[str] = mapped_column(String(32), ForeignKey("alert.id"))
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20))
    actor: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    alert = relationship("Alert", back_populates="history")


class Notification(Base):
    __tablename__ = "notification"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    alert_id: Mapped[str] = mapped_column(String(32), ForeignKey("alert.id"))
    channel: Mapped[str] = mapped_column(String(20))  # email|sms|push|webhook|voice
    target: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    idempotency_key: Mapped[str] = mapped_column(String(80))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    alert = relationship("Alert", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
