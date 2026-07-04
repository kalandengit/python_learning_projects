"""QR envelope: roundtrip, tamper, freshness, no PII, PNG rendering."""

from __future__ import annotations

import secrets
import time
import uuid

import pytest

from app.services.qr_service import QRInvalid, QRService, owner_hash

SECRET = secrets.token_bytes(32)


@pytest.fixture()
def qr() -> QRService:
    return QRService(SECRET, max_age_seconds=90)


def test_roundtrip(qr: QRService) -> None:
    event_id, owner_id = uuid.uuid4(), uuid.uuid4()
    data = qr.issue("tok123", event_id, owner_id)
    envelope = qr.verify(data)
    assert envelope.qr_token == "tok123"
    assert envelope.event_id == event_id
    assert envelope.owner_hash == owner_hash(owner_id)


def test_no_pii_in_qr(qr: QRService) -> None:
    owner_id = uuid.uuid4()
    data = qr.issue("tok", uuid.uuid4(), owner_id)
    assert owner_id.hex not in data
    assert str(owner_id) not in data


def test_tampered_mac_rejected(qr: QRService) -> None:
    data = qr.issue("tok", uuid.uuid4(), uuid.uuid4())
    head, _, mac = data.rpartition(".")
    flipped = ("A" if mac[0] != "A" else "B") + mac[1:]
    with pytest.raises(QRInvalid) as exc:
        qr.verify(f"{head}.{flipped}")
    assert exc.value.reason == "bad_mac"


def test_tampered_payload_rejected(qr: QRService) -> None:
    prefix, _payload, mac = qr.issue("tok", uuid.uuid4(), uuid.uuid4()).split(".")
    other_payload = qr.issue("other", uuid.uuid4(), uuid.uuid4()).split(".")[1]
    with pytest.raises(QRInvalid) as exc:
        qr.verify(f"{prefix}.{other_payload}.{mac}")
    assert exc.value.reason == "bad_mac"


def test_stale_envelope_rejected(qr: QRService) -> None:
    data = qr.issue("tok", uuid.uuid4(), uuid.uuid4(), now=time.time() - 3600)
    with pytest.raises(QRInvalid) as exc:
        qr.verify(data)
    assert exc.value.reason == "stale"


def test_future_envelope_rejected(qr: QRService) -> None:
    data = qr.issue("tok", uuid.uuid4(), uuid.uuid4(), now=time.time() + 3600)
    with pytest.raises(QRInvalid) as exc:
        qr.verify(data)
    assert exc.value.reason == "future_timestamp"


def test_wrong_secret_rejected(qr: QRService) -> None:
    other = QRService(secrets.token_bytes(32), max_age_seconds=90)
    data = other.issue("tok", uuid.uuid4(), uuid.uuid4())
    with pytest.raises(QRInvalid):
        qr.verify(data)


def test_bad_format_rejected(qr: QRService) -> None:
    for garbage in ("", "nope", "EMS3.only-two", "WRONG.a.b"):
        with pytest.raises(QRInvalid):
            qr.verify(garbage)


def test_render_png(qr: QRService) -> None:
    data = qr.issue("tok", uuid.uuid4(), uuid.uuid4())
    png = qr.render_png(data)
    assert png.startswith(b"\x89PNG\r\n")
