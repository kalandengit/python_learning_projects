"""Pydantic request/response schemas (API contract)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "operator"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    role: str
    active: bool


class SiteCreate(BaseModel):
    name: str
    lat: float | None = None
    lon: float | None = None


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    lat: float | None
    lon: float | None


class ZoneCreate(BaseModel):
    site_id: str
    name: str
    geometry: dict | None = None


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    name: str
    geometry: dict | None


class CameraCreate(BaseModel):
    site_id: str
    name: str
    ip_address: str | None = None
    protocol: str = "ONVIF"
    model: str | None = None
    orientation: str | None = None
    fov_angle: float | None = None
    zone_ids: list[str] = Field(default_factory=list)


class CameraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    name: str
    ip_address: str | None
    protocol: str
    model: str | None
    status: str
    last_seen: datetime | None


class DetectionEventIn(BaseModel):
    """Payload a camera/gateway posts on detection."""

    camera_id: str
    object_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    ts: datetime | None = None
    bbox: dict | None = None
    track_id: str | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    camera_id: str
    object_class: str
    confidence: float
    ts: datetime
    idempotency_key: str


class IngestResult(BaseModel):
    status: str  # "duplicate" | "ignored" | "false_positive" | "intrusion"
    event_id: str | None = None
    alert_id: str | None = None
    decision: str | None = None
    matched_rule: str | None = None


class RuleIn(BaseModel):
    name: str
    priority: int = 100
    conditions: list[dict] = Field(default_factory=list)
    action: dict
    enabled: bool = True


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    priority: int
    conditions: list
    action: dict
    enabled: bool
    version: int


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    camera_id: str
    zone_id: str | None
    type: str
    criticality: str
    status: str
    created_at: datetime


class AlertStatusUpdate(BaseModel):
    status: str  # IN_PROGRESS|ACKNOWLEDGED|CLOSED|FALSE_POSITIVE
    reason: str | None = None


class DashboardStats(BaseModel):
    cameras_total: int
    cameras_online: int
    cameras_offline: int
    intrusions_today: int
    critical_alerts: int
    open_alerts: int
