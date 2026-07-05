"""Attachment storage and malware scanning abstractions.

These are deliberately thin interfaces. In production ``store_blob`` writes to
object storage (encrypting medical documents at rest) and ``scan_blob`` calls
an async malware scanner (e.g. ClamAV) whose verdict flips the attachment to
CLEAN/INFECTED. For local/dev and tests they are simple, synchronous stubs.
"""

from __future__ import annotations

import uuid

from ..models import ScanStatus


def store_blob(filename: str, data: bytes, *, encrypt: bool) -> str:
    """Persist bytes and return an opaque storage key. Stub: no real I/O."""
    return f"blob://{uuid.uuid4().hex}/{filename}"


# A tiny EICAR-like sentinel lets tests exercise the infected path deterministically.
_MALWARE_SIGNATURE = b"STAFFHUB-EICAR-TEST"


def scan_blob(data: bytes) -> ScanStatus:
    """Return the scan verdict for the given bytes."""
    if _MALWARE_SIGNATURE in data:
        return ScanStatus.INFECTED
    return ScanStatus.CLEAN
