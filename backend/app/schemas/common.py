from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ShiftCreate(BaseModel):
    user_id: str
    title: str = "Shift"
    location: str | None = None
    starts_at: datetime
    ends_at: datetime
    published: bool = False


class ShiftOut(BaseModel):
    id: str
    user_id: str
    title: str
    location: str | None
    starts_at: datetime
    ends_at: datetime
    published: bool

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    deep_link: str | None
    is_read: bool
    is_archived: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagIn(BaseModel):
    key: str
    enabled: bool


class FeatureFlagOut(BaseModel):
    key: str
    enabled: bool

    model_config = {"from_attributes": True}


class TimelineEntry(BaseModel):
    kind: str  # shift | request | notification
    id: str
    title: str
    at: datetime
    detail: str | None = None
    deep_link: str | None = None


class BulkShiftAction(BaseModel):
    shift_ids: list[str]
    action: str  # publish | archive | delete


class AuditLogOut(BaseModel):
    id: str
    actor_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    ip: str | None
    device: str | None
    reason: str | None
    before_state: dict | None
    after_state: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PurgeResult(BaseModel):
    purged: dict[str, int]
    retention_days: int
