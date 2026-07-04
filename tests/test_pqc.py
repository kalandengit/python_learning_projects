"""Hybrid PQC signer: roundtrip, tamper, downgrade resistance, aliases."""

from __future__ import annotations

import secrets

import pytest

from app.core.pqc import (
    ALGORITHM_ALIASES,
    HAS_OQS,
    HybridSigner,
    PQCError,
    canonical_algorithm,
)

HMAC_KEY = secrets.token_bytes(32)


def make_signer() -> HybridSigner:
    return HybridSigner(HMAC_KEY, allow_hmac_only=not HAS_OQS)


def test_sign_verify_roundtrip() -> None:
    signer = make_signer()
    payload = b'{"e":"evt","t":"tok","u":"hash"}'
    blob = signer.sign(payload)
    assert signer.verify(payload, blob)


def test_tampered_payload_rejected() -> None:
    signer = make_signer()
    blob = signer.sign(b"payload-A")
    assert not signer.verify(b"payload-B", blob)


def test_tampered_blob_rejected() -> None:
    signer = make_signer()
    payload = b"payload"
    blob = bytearray(signer.sign(payload))
    blob[10] ^= 0xFF  # flip a MAC byte
    assert not signer.verify(payload, bytes(blob))


def test_truncated_and_garbage_blobs_rejected() -> None:
    signer = make_signer()
    assert not signer.verify(b"p", b"")
    assert not signer.verify(b"p", b"EMS3")
    assert not signer.verify(b"p", b"XXXX" + b"\x01" + b"\x00" * 40)


def test_downgrade_to_hmac_only_rejected() -> None:
    """Stripping the ML-DSA layer and flipping alg to 0 must fail the MAC."""
    signer = make_signer()
    payload = b"payload"
    if HAS_OQS:
        mldsa_blob = signer.sign(payload)
    else:
        # Reconstruct what a PQC-enabled peer would have produced: the MAC
        # covers the alg byte, which is all this test needs.
        mldsa_blob = b"EMS3" + bytes([0x01]) + signer._mac(0x01, payload) + b"fake-sig"
    mac = mldsa_blob[5:37]
    forged = b"EMS3" + bytes([0x00]) + mac  # alg byte changed, sig stripped
    assert not signer.verify(payload, forged)


def test_algorithm_aliases_legacy_dilithium() -> None:
    assert canonical_algorithm("Dilithium3") == "ML-DSA-65"
    assert ALGORITHM_ALIASES["Dilithium3"] == "ML-DSA-65"
    assert canonical_algorithm("ML-DSA-65") == "ML-DSA-65"
    with pytest.raises(PQCError):
        canonical_algorithm("RSA-2048")


def test_weak_hmac_key_rejected() -> None:
    with pytest.raises(PQCError):
        HybridSigner(b"short", allow_hmac_only=True)


@pytest.mark.skipif(HAS_OQS, reason="exercises the no-liboqs failure path")
def test_pqc_required_without_liboqs_raises() -> None:
    with pytest.raises(PQCError):
        HybridSigner(HMAC_KEY, allow_hmac_only=False)


@pytest.mark.skipif(not HAS_OQS, reason="liboqs not installed")
def test_mldsa_signature_present_and_verifies() -> None:
    signer = HybridSigner(HMAC_KEY)
    payload = b"payload"
    blob = signer.sign(payload)
    assert blob[4] == 0x01  # ML-DSA alg byte
    assert len(blob) > 4 + 1 + 32 + 3000  # ML-DSA-65 signature is 3309 bytes
    assert signer.verify(payload, blob)
