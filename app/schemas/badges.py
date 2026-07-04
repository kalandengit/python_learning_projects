"""Badge schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import BadgeType, ScanResult


class BadgeCreate(BaseModel):
    event_id: uuid.UUID
    holder_name: str = Field(min_length=1, max_length=200)
    type: BadgeType
    access_zones: list[str] = Field(default_factory=list, max_length=50)
    valid_from: datetime
    valid_until: datetime
    user_id: uuid.UUID | None = None
    nfc_uid: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _check(self) -> BadgeCreate:
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        return self


class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    holder_name: str
    type: BadgeType
    access_zones: list[str]
    nfc_uid: str | None
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    created_at: datetime


class BadgeValidateRequest(BaseModel):
    qr_data: str = Field(max_length=4096)
    device_id: str = Field(min_length=1, max_length=120)
    zone: str | None = Field(default=None, max_length=120)


class BadgeValidateResponse(BaseModel):
    result: ScanResult
    badge_id: uuid.UUID
    badge_type: BadgeType
    holder_name: str
    zone: str | None
