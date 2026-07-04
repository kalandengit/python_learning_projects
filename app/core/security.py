"""Passwords (Argon2id + legacy bcrypt rehash), JWT (PyJWT RS256), refresh
rotation with reuse detection, account lockout, TOTP secret encryption.

Error messages surfaced to clients are always generic — no user enumeration,
no token internals. Secrets and tokens are never logged.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import logging
import os
import uuid
from collections.abc import Awaitable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt as _bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from valkey.asyncio import Valkey

from app.models.base import UserRole

logger = logging.getLogger(__name__)

# --- Passwords: Argon2id m=19456 KiB, t=2, p=1 (locked, §2) -------------------

_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
# Constant-cost dummy verify target for unknown users (anti-enumeration timing).
_DUMMY_HASH = _hasher.hash("ems-dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """Return (valid, needs_rehash). Accepts legacy bcrypt hashes ($2*$)."""
    if stored_hash.startswith("$2"):
        ok = _bcrypt.checkpw(password.encode(), stored_hash.encode())
        return ok, ok  # rehash to Argon2id transparently on next successful login
    try:
        _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False, False
    return True, _hasher.check_needs_rehash(stored_hash)


def dummy_verify() -> None:
    """Burn the same time as a real verify — call when the user doesn't exist."""
    with contextlib.suppress(VerifyMismatchError):
        _hasher.verify(_DUMMY_HASH, "not-the-password")


# --- JWT (RS256; access 15 min / refresh 7 d / mfa 5 min) ----------------------

_ISSUER = "ems"


class TokenError(Exception):
    """Invalid, expired or mistyped token — always mapped to a generic 401."""


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    family: str


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    org_id: uuid.UUID
    role: UserRole


class TokenIssuer:
    def __init__(
        self,
        private_pem: bytes,
        public_pem: bytes,
        *,
        access_ttl: int,
        refresh_ttl: int,
        mfa_ttl: int,
    ) -> None:
        self._private_pem = private_pem
        self._public_pem = public_pem
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._mfa_ttl = mfa_ttl

    def _encode(self, claims: dict[str, Any], ttl: int) -> str:
        now = datetime.now(UTC)
        claims |= {
            "iss": _ISSUER,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(claims, self._private_pem, algorithm="RS256")

    def issue_access(self, user_id: uuid.UUID, org_id: uuid.UUID, role: UserRole) -> str:
        return self._encode(
            {"sub": str(user_id), "org": str(org_id), "role": role.value, "typ": "access"},
            self._access_ttl,
        )

    def issue_refresh(
        self, user_id: uuid.UUID, org_id: uuid.UUID, role: UserRole, family: str
    ) -> str:
        return self._encode(
            {
                "sub": str(user_id),
                "org": str(org_id),
                "role": role.value,
                "typ": "refresh",
                "fam": family,
            },
            self._refresh_ttl,
        )

    def issue_pair(self, user_id: uuid.UUID, org_id: uuid.UUID, role: UserRole) -> TokenPair:
        family = uuid.uuid4().hex
        return TokenPair(
            access_token=self.issue_access(user_id, org_id, role),
            refresh_token=self.issue_refresh(user_id, org_id, role, family),
            family=family,
        )

    def issue_mfa(self, user_id: uuid.UUID) -> str:
        return self._encode({"sub": str(user_id), "typ": "mfa"}, self._mfa_ttl)

    def decode(self, token: str, expected_typ: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._public_pem,
                algorithms=["RS256"],
                issuer=_ISSUER,
                options={"require": ["exp", "iat", "sub", "typ"]},
            )
        except jwt.InvalidTokenError as exc:
            raise TokenError("invalid token") from exc
        if claims.get("typ") != expected_typ:
            raise TokenError("wrong token type")
        return claims

    def auth_context(self, claims: dict[str, Any]) -> AuthContext:
        try:
            return AuthContext(
                user_id=uuid.UUID(claims["sub"]),
                org_id=uuid.UUID(claims["org"]),
                role=UserRole(claims["role"]),
            )
        except (KeyError, ValueError) as exc:
            raise TokenError("malformed claims") from exc


# --- Refresh rotation + reuse detection (Valkey allowlist, §2) ------------------

_ROTATE_LUA = """
local cur = redis.call('GET', KEYS[1])
if not cur then return 0 end
if cur == ARGV[1] then
    redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
    return 1
end
redis.call('DEL', KEYS[1])
return -1
"""


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SessionStore:
    """Refresh-token family allowlist + lockout counters, backed by Valkey."""

    def __init__(self, client: Valkey, *, refresh_ttl: int, lockout_max: int, lockout_ttl: int):
        self._v = client
        self._refresh_ttl = refresh_ttl
        self._lockout_max = lockout_max
        self._lockout_ttl = lockout_ttl

    @staticmethod
    def _fam_key(family: str) -> str:
        return f"rtfam:{family}"

    @staticmethod
    def _user_fams_key(user_id: uuid.UUID) -> str:
        return f"userfams:{user_id}"

    async def register_family(self, user_id: uuid.UUID, family: str, refresh_token: str) -> None:
        fp = _token_fingerprint(refresh_token)
        async with self._v.pipeline(transaction=True) as pipe:
            pipe.set(self._fam_key(family), fp, ex=self._refresh_ttl)
            pipe.sadd(self._user_fams_key(user_id), family)
            pipe.expire(self._user_fams_key(user_id), self._refresh_ttl)
            await pipe.execute()

    async def rotate(self, family: str, old_token: str, new_token: str) -> int:
        """1 = rotated, 0 = unknown/expired family, -1 = REUSE (family revoked)."""
        result = await self._v.eval(  # type: ignore[misc]
            _ROTATE_LUA,
            1,
            self._fam_key(family),
            _token_fingerprint(old_token),
            _token_fingerprint(new_token),
            str(self._refresh_ttl),
        )
        code = int(result)
        if code == -1:
            # Security event — family id only; never the token itself.
            logger.warning("refresh token REUSE detected; family %s revoked", family)
        return code

    async def revoke_family(self, family: str) -> None:
        await self._v.delete(self._fam_key(family))

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        key = self._user_fams_key(user_id)
        raw = await cast("Awaitable[set[bytes | str]]", self._v.smembers(key))
        families = [f.decode() if isinstance(f, bytes) else f for f in raw]
        if families:
            await self._v.delete(*[self._fam_key(f) for f in families])
        await self._v.delete(key)

    # --- Account lockout: 5 fails → 15 min (§2) --------------------------------

    @staticmethod
    def _lock_key(email: str) -> str:
        return "lockout:" + hashlib.sha256(email.lower().encode()).hexdigest()

    async def is_locked(self, email: str) -> bool:
        count = await self._v.get(self._lock_key(email))
        return count is not None and int(count) >= self._lockout_max

    async def record_failure(self, email: str) -> None:
        key = self._lock_key(email)
        async with self._v.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, self._lockout_ttl)
            await pipe.execute()

    async def clear_failures(self, email: str) -> None:
        await self._v.delete(self._lock_key(email))


# --- TOTP secret encryption at rest (AES-256-GCM) --------------------------------

_TOTP_AAD = b"ems-totp-v3"


def encrypt_totp_secret(key: bytes, secret: str) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, secret.encode(), _TOTP_AAD)


def decrypt_totp_secret(key: bytes, blob: bytes) -> str:
    return AESGCM(key).decrypt(blob[:12], blob[12:], _TOTP_AAD).decode()


def new_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode().rstrip("=")
