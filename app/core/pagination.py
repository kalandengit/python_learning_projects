"""Cursor pagination: base64("created_at|id") — never OFFSET (§2)."""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime


class CursorError(ValueError):
    """Malformed cursor — mapped to a 422 with a generic message."""


def encode_cursor(created_at: datetime, item_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        created_str, id_str = raw.split("|", 1)
        return datetime.fromisoformat(created_str), uuid.UUID(id_str)
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise CursorError("invalid cursor") from exc
