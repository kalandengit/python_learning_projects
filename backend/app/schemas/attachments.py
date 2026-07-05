from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..models import ScanStatus


class AttachmentOut(BaseModel):
    id: str
    request_id: str
    filename: str
    content_type: str
    size_bytes: int
    scan_status: ScanStatus
    is_medical: bool
    is_available: bool
    created_at: datetime

    model_config = {"from_attributes": True}
