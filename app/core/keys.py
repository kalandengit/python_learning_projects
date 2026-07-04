"""Key material resolution.

Prod/staging: every key MUST come from configuration (AWS Secrets Manager →
env). Dev/test: missing keys are generated ephemerally so the stack boots
without secrets on disk. Key material is never logged.
"""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import Settings


@dataclass(frozen=True)
class KeyMaterial:
    jwt_private_pem: bytes
    jwt_public_pem: bytes
    qr_hmac_secret: bytes
    totp_enc_key: bytes


def _generate_rsa_pair() -> tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return priv, pub


def _require_dev(settings: Settings, what: str) -> None:
    if not settings.is_dev_like:
        raise RuntimeError(f"{what} must be configured in {settings.env} (Secrets Manager)")


def resolve_keys(settings: Settings) -> KeyMaterial:
    if settings.jwt_private_key_pem is not None and settings.jwt_public_key_pem is not None:
        jwt_priv = settings.jwt_private_key_pem.get_secret_value().encode()
        jwt_pub = settings.jwt_public_key_pem.encode()
    else:
        _require_dev(settings, "EMS_JWT_PRIVATE_KEY_PEM / EMS_JWT_PUBLIC_KEY_PEM")
        jwt_priv, jwt_pub = _generate_rsa_pair()

    if settings.qr_hmac_secret is not None:
        raw = settings.qr_hmac_secret.get_secret_value()
        try:
            qr_secret = base64.b64decode(raw, validate=True)
        except Exception:
            qr_secret = raw.encode()
        if len(qr_secret) < 32:
            raise RuntimeError("EMS_QR_HMAC_SECRET must be at least 32 bytes")
    else:
        _require_dev(settings, "EMS_QR_HMAC_SECRET")
        qr_secret = secrets.token_bytes(32)

    if settings.totp_enc_key_b64 is not None:
        totp_key = settings.totp_enc_key()
    else:
        _require_dev(settings, "EMS_TOTP_ENC_KEY_B64")
        totp_key = secrets.token_bytes(32)

    return KeyMaterial(
        jwt_private_pem=jwt_priv,
        jwt_public_pem=jwt_pub,
        qr_hmac_secret=qr_secret,
        totp_enc_key=totp_key,
    )


_cache: dict[int, KeyMaterial] = {}


def get_key_material(settings: Settings) -> KeyMaterial:
    key = id(settings)
    if key not in _cache:
        _cache[key] = resolve_keys(settings)
    return _cache[key]
