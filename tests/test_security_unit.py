"""Password hashing (Argon2id + bcrypt legacy), JWTs, cursor codec."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import bcrypt
import pytest

from app.core import security
from app.core.keys import _generate_rsa_pair
from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.core.security import TokenError, TokenIssuer
from app.models import UserRole


def test_argon2_roundtrip() -> None:
    h = security.hash_password("s3cret-enough-long")
    assert h.startswith("$argon2id$")
    assert "m=19456,t=2,p=1" in h
    valid, rehash = security.verify_password("s3cret-enough-long", h)
    assert valid and not rehash


def test_argon2_wrong_password() -> None:
    h = security.hash_password("right")
    assert security.verify_password("wrong", h) == (False, False)


def test_legacy_bcrypt_verifies_and_flags_rehash() -> None:
    legacy = bcrypt.hashpw(b"old-password", bcrypt.gensalt(rounds=4)).decode()
    valid, rehash = security.verify_password("old-password", legacy)
    assert valid and rehash  # transparent Argon2id rehash on login (§2)
    assert security.verify_password("bad", legacy) == (False, False)


def test_totp_secret_encryption_roundtrip() -> None:
    key = b"k" * 32
    secret = security.new_totp_secret()
    blob = security.encrypt_totp_secret(key, secret)
    assert secret.encode() not in blob  # encrypted at rest
    assert security.decrypt_totp_secret(key, blob) == secret


@pytest.fixture(scope="module")
def issuer() -> TokenIssuer:
    priv, pub = _generate_rsa_pair()
    return TokenIssuer(priv, pub, access_ttl=900, refresh_ttl=604800, mfa_ttl=300)


def test_jwt_access_roundtrip(issuer: TokenIssuer) -> None:
    uid, org = uuid.uuid4(), uuid.uuid4()
    token = issuer.issue_access(uid, org, UserRole.ATTENDEE)
    ctx = issuer.auth_context(issuer.decode(token, "access"))
    assert (ctx.user_id, ctx.org_id, ctx.role) == (uid, org, UserRole.ATTENDEE)


def test_jwt_type_confusion_rejected(issuer: TokenIssuer) -> None:
    refresh = issuer.issue_refresh(uuid.uuid4(), uuid.uuid4(), UserRole.ATTENDEE, "fam1")
    with pytest.raises(TokenError):
        issuer.decode(refresh, "access")  # refresh token can't act as access


def test_jwt_expired_rejected() -> None:
    priv, pub = _generate_rsa_pair()
    expired_issuer = TokenIssuer(priv, pub, access_ttl=-10, refresh_ttl=1, mfa_ttl=1)
    token = expired_issuer.issue_access(uuid.uuid4(), uuid.uuid4(), UserRole.ATTENDEE)
    with pytest.raises(TokenError):
        expired_issuer.decode(token, "access")


def test_jwt_garbage_rejected(issuer: TokenIssuer) -> None:
    with pytest.raises(TokenError):
        issuer.decode("not.a.jwt", "access")


def test_cursor_roundtrip() -> None:
    now = datetime.now(UTC)
    item = uuid.uuid4()
    created, decoded_id = decode_cursor(encode_cursor(now, item))
    assert (created, decoded_id) == (now, item)


@pytest.mark.parametrize("bad", ["", "!!!!", "bm90LWEtY3Vyc29y", "YXxi"])
def test_cursor_invalid(bad: str) -> None:
    with pytest.raises(CursorError):
        decode_cursor(bad)
