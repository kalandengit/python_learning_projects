"""Signed QR envelopes (segno).

QR content:  ``EMS3.<b64url(payload)>.<b64url(hmac_sha256)>``
payload:     canonical JSON ``{"e": event_id, "t": qr_token, "u": owner_hash, "ts": epoch}``

* No PII in the QR — the owner appears only as SHA-256(owner UUID bytes) (§2).
* ``ts`` is refreshed by the client every ≤60 s; stale or future envelopes are
  rejected (max_age includes 30 s clock-skew allowance).
* The hybrid ML-DSA-65 signature over the static payload {t,e,u} is stored
  server-side at issuance (see core.pqc) — it does not fit in a QR code.
* The PNG endpoint must send ``Cache-Control: no-store``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import time
import uuid
from dataclasses import dataclass

import segno

_PREFIX = "EMS3"
_MAC_INFO = b"EMS-QR3|"
_SKEW_SECONDS = 30


class QRInvalid(Exception):
    """Envelope failed verification; `reason` is for the scan log, not clients."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class QREnvelope:
    qr_token: str
    event_id: uuid.UUID
    owner_hash: str
    issued_at: int


def owner_hash(owner_id: uuid.UUID) -> str:
    return hashlib.sha256(owner_id.bytes).hexdigest()


def static_payload(qr_token: str, event_id: uuid.UUID, owner_id: uuid.UUID) -> bytes:
    """Canonical bytes signed by the hybrid PQC signer at issuance."""
    return json.dumps(
        {"e": str(event_id), "t": qr_token, "u": owner_hash(owner_id)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


class QRService:
    def __init__(self, hmac_secret: bytes, *, max_age_seconds: int) -> None:
        self._secret = hmac_secret
        self._max_age = max_age_seconds

    def _mac(self, payload_b64: str) -> bytes:
        return hmac.new(self._secret, _MAC_INFO + payload_b64.encode(), hashlib.sha256).digest()

    def issue(
        self,
        qr_token: str,
        event_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        now: float | None = None,
    ) -> str:
        payload = {
            "e": str(event_id),
            "t": qr_token,
            "u": owner_hash(owner_id),
            "ts": int(now if now is not None else time.time()),
        }
        payload_b64 = _b64e(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        return f"{_PREFIX}.{payload_b64}.{_b64e(self._mac(payload_b64))}"

    def verify(self, qr_data: str, *, now: float | None = None) -> QREnvelope:
        parts = qr_data.split(".")
        if len(parts) != 3 or parts[0] != _PREFIX:
            raise QRInvalid("bad_format")
        _, payload_b64, mac_b64 = parts
        try:
            presented_mac = _b64d(mac_b64)
        except Exception as exc:
            raise QRInvalid("bad_format") from exc
        if not hmac.compare_digest(presented_mac, self._mac(payload_b64)):
            raise QRInvalid("bad_mac")
        try:
            payload = json.loads(_b64d(payload_b64))
            envelope = QREnvelope(
                qr_token=str(payload["t"]),
                event_id=uuid.UUID(str(payload["e"])),
                owner_hash=str(payload["u"]),
                issued_at=int(payload["ts"]),
            )
        except Exception as exc:
            raise QRInvalid("bad_payload") from exc
        ts_now = now if now is not None else time.time()
        if envelope.issued_at > ts_now + _SKEW_SECONDS:
            raise QRInvalid("future_timestamp")
        if ts_now - envelope.issued_at > self._max_age:
            raise QRInvalid("stale")
        return envelope

    @staticmethod
    def render_png(qr_data: str, *, scale: int = 6) -> bytes:
        buf = io.BytesIO()
        segno.make(qr_data, error="m").save(buf, kind="png", scale=scale)
        return buf.getvalue()
