"""Ticket purchase / listing / validation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import PaymentStatus, ScanResult, TicketStatus


class PurchaseRequest(BaseModel):
    tier_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=10)


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    tier_id: uuid.UUID
    status: TicketStatus
    created_at: datetime
    used_at: datetime | None


class PurchaseResponse(BaseModel):
    payment_id: uuid.UUID
    payment_status: PaymentStatus
    amount_cents: int
    currency: str
    tickets: list[TicketOut]
    checkout_url: str | None  # None for FREE tiers (instant issuance)
    reused: bool


class TicketPage(BaseModel):
    items: list[TicketOut]
    next_cursor: str | None


class ValidateRequest(BaseModel):
    qr_data: str = Field(max_length=4096)
    device_id: str = Field(min_length=1, max_length=120)
    zone: str | None = Field(default=None, max_length=120)


class ValidateResponse(BaseModel):
    result: ScanResult
    ticket_id: uuid.UUID | None
    event_id: uuid.UUID | None
    used_at: datetime | None
