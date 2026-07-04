"""Hybrid post-quantum signer: ML-DSA-65 (FIPS 204, liboqs) + HMAC-SHA256.

Signature blob layout (stored in tickets.pqc_signature / badges.pqc_signature):

    b"EMS3" | alg (1 byte) | mac (32 bytes) | mldsa_signature (variable)

* alg 0x00 = HMAC-only (dev/test without liboqs), 0x01 = ML-DSA-65.
* The MAC covers ``alg || payload`` so an attacker cannot strip the ML-DSA
  signature and downgrade the blob to HMAC-only.
* An ML-DSA-65 signature is 3 309 bytes — larger than a QR code can carry
  (2 953-byte max), so the hybrid signature never travels inside the QR.
  It is generated at issuance over the static payload {t,e,u} and verified
  server-side on every scan; the QR itself carries the HMAC envelope with
  the refreshing timestamp (see qr_service).
* ALGORITHM_ALIASES maps legacy Dilithium names on tokens issued before the
  FIPS 204 rename. ML-KEM-768 is reserved for future encrypted payloads.
"""

from __future__ import annotations

import hashlib
import hmac
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

try:  # liboqs ≥0.12 — compiled into the Docker image; optional in dev/test
    import oqs

    HAS_OQS = True
except ImportError:  # pragma: no cover - exercised only without liboqs
    oqs = None
    HAS_OQS = False

ALGORITHM_ALIASES: dict[str, str] = {
    "Dilithium2": "ML-DSA-44",
    "Dilithium3": "ML-DSA-65",
    "Dilithium5": "ML-DSA-87",
    "ML-DSA-44": "ML-DSA-44",
    "ML-DSA-65": "ML-DSA-65",
    "ML-DSA-87": "ML-DSA-87",
}
RESERVED_KEM = "ML-KEM-768"

_MAGIC = b"EMS3"
_ALG_HMAC_ONLY = 0x00
_ALG_ML_DSA = 0x01
_MAC_LEN = 32


class PQCError(Exception):
    """Configuration/availability problem with the hybrid signer."""


def canonical_algorithm(name: str) -> str:
    try:
        return ALGORITHM_ALIASES[name]
    except KeyError as exc:
        raise PQCError(f"unsupported signature algorithm: {name}") from exc


class HybridSigner:
    """Signs and verifies static QR payloads with ML-DSA-65 + HMAC-SHA256."""

    def __init__(
        self,
        hmac_key: bytes,
        *,
        algorithm: str = "ML-DSA-65",
        secret_key: bytes | None = None,
        public_key: bytes | None = None,
        allow_hmac_only: bool = False,
    ) -> None:
        if len(hmac_key) < 32:
            raise PQCError("hybrid signer HMAC key must be at least 32 bytes")
        self._hmac_key = hmac_key
        self.algorithm = canonical_algorithm(algorithm)
        self._secret_key = secret_key
        self.public_key = public_key
        self._hmac_only = False

        if HAS_OQS:
            if self._secret_key is None:
                # Dev convenience: ephemeral keypair. Prod supplies both keys.
                with oqs.Signature(self.algorithm) as sig:
                    self.public_key = sig.generate_keypair()
                    self._secret_key = sig.export_secret_key()
                logger.warning("PQC: generated ephemeral %s keypair (dev only)", self.algorithm)
            elif self.public_key is None:
                raise PQCError("pqc_public_key is required when pqc_secret_key is set")
        elif allow_hmac_only:
            self._hmac_only = True
            logger.warning("PQC: liboqs unavailable — HMAC-only mode (dev/test only)")
        else:
            raise PQCError(
                "liboqs is not available and EMS_PQC_ALLOW_HMAC_ONLY is false; "
                "install the 'pqc' extra / compile liboqs"
            )

    def _mac(self, alg: int, payload: bytes) -> bytes:
        return hmac.new(self._hmac_key, bytes([alg]) + payload, hashlib.sha256).digest()

    def sign(self, payload: bytes) -> bytes:
        if self._hmac_only:
            alg = _ALG_HMAC_ONLY
            sig = b""
        else:
            alg = _ALG_ML_DSA
            assert self._secret_key is not None
            with oqs.Signature(self.algorithm, secret_key=self._secret_key) as signer:
                sig = signer.sign(payload)
        return _MAGIC + bytes([alg]) + self._mac(alg, payload) + sig

    def verify(self, payload: bytes, blob: bytes) -> bool:
        if len(blob) < len(_MAGIC) + 1 + _MAC_LEN or not blob.startswith(_MAGIC):
            return False
        alg = blob[len(_MAGIC)]
        mac = blob[len(_MAGIC) + 1 : len(_MAGIC) + 1 + _MAC_LEN]
        sig = blob[len(_MAGIC) + 1 + _MAC_LEN :]

        # HMAC layer first — covers alg byte, so downgrade attempts fail here.
        if not hmac.compare_digest(mac, self._mac(alg, payload)):
            return False

        if alg == _ALG_HMAC_ONLY:
            # Only acceptable when this deployment explicitly runs HMAC-only.
            return self._hmac_only and not sig
        if alg != _ALG_ML_DSA:
            return False
        if self._hmac_only:
            # Blob was produced by a PQC-enabled signer; we cannot check the
            # ML-DSA layer without liboqs, but the HMAC layer already passed.
            return True
        if self.public_key is None or not sig:
            return False
        with oqs.Signature(self.algorithm) as verifier:
            result: bool = verifier.verify(payload, sig, self.public_key)
            return result


_signer_cache: dict[int, HybridSigner] = {}


def get_hybrid_signer(settings: Settings, hmac_key: bytes) -> HybridSigner:
    key = id(settings)
    if key not in _signer_cache:
        import base64

        if not settings.is_dev_like and settings.pqc_allow_hmac_only:
            raise PQCError("EMS_PQC_ALLOW_HMAC_ONLY must be false outside dev/test")
        secret = (
            base64.b64decode(settings.pqc_secret_key_b64.get_secret_value())
            if settings.pqc_secret_key_b64
            else None
        )
        public = (
            base64.b64decode(settings.pqc_public_key_b64) if settings.pqc_public_key_b64 else None
        )
        _signer_cache[key] = HybridSigner(
            hmac_key,
            algorithm=settings.pqc_algorithm,
            secret_key=secret,
            public_key=public,
            allow_hmac_only=settings.pqc_allow_hmac_only,
        )
    return _signer_cache[key]
