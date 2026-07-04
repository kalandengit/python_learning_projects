"""Event and tier schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime
    venue_name: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    geofence_radius_m: int | None = Field(default=None, gt=0, le=100_000)

    @model_validator(mode="after")
    def _check(self) -> EventCreate:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class TierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_cents: int = Field(ge=0)  # 0 = FREE
    currency: str = Field(default="eur", pattern="^[a-z]{3}$")
    capacity: int = Field(ge=0)
    sales_starts_at: datetime | None = None
    sales_ends_at: datetime | None = None


class TierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    price_cents: int
    currency: str
    capacity: int
    sold_count: int
    sales_starts_at: datetime | None
    sales_ends_at: datetime | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    venue_name: str | None
    latitude: float | None = None
    longitude: float | None = None
    geofence_radius_m: int | None
    is_published: bool
    version: int
    created_at: datetime


class EventPage(BaseModel):
    items: list[EventOut]
    next_cursor: str | None
