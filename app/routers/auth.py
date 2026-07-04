"""Auth: register, login (+TOTP MFA), refresh rotation, logout.

Every failure path returns the same generic message with the same status —
no account enumeration by status code, body, or (via dummy_verify) timing.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core import security
from app.core.deps import (
    get_app_settings,
    get_auth,
    get_optional_auth,
    get_session_store,
    get_token_issuer,
    rate_limit_ip,
)
from app.core.keys import get_key_material
from app.core.security import (
    AuthContext,
    SessionStore,
    TokenError,
    TokenIssuer,
)
from app.db import get_session
from app.models import Organization, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MFARequiredResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)
_REGISTRATION_FAILED = HTTPException(
    status.HTTP_400_BAD_REQUEST, detail="Registration could not be completed"
)
_LOCKED = HTTPException(
    status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, try again later"
)

PUBLIC_ORG_NAME = "public"


async def _issue_tokens(
    issuer: TokenIssuer, store: SessionStore, user: User
) -> TokenResponse:
    pair = issuer.issue_pair(user.id, user.organization_id, user.role)
    await store.register_family(user.id, pair.family, pair.refresh_token)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=issuer.access_ttl,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_ip("register"))],
)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> TokenResponse:
    email = body.email.lower()
    if body.organization_name is not None:
        org = Organization(name=body.organization_name)
        session.add(org)
        role = UserRole.EVENT_ORGANIZER
    else:
        existing_org = await session.scalar(
            select(Organization).where(Organization.name == PUBLIC_ORG_NAME)
        )
        org = existing_org or Organization(name=PUBLIC_ORG_NAME)
        if existing_org is None:
            session.add(org)
        role = UserRole.ATTENDEE

    user = User(
        organization=org,
        email=email,
        full_name=body.full_name,
        password_hash=security.hash_password(body.password),
        role=role,
        marketing_consent=body.marketing_consent,
        terms_accepted_at=datetime.now(UTC),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # Duplicate email or org name — same generic answer either way.
        await session.rollback()
        raise _REGISTRATION_FAILED from None
    return await _issue_tokens(issuer, store, user)


@router.post(
    "/login",
    response_model=TokenResponse | MFARequiredResponse,
    dependencies=[Depends(rate_limit_ip("login"))],
)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> TokenResponse | MFARequiredResponse:
    email = body.email.lower()
    if await store.is_locked(email):
        raise _LOCKED

    user = await session.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None or not user.is_active:
        security.dummy_verify()  # equalise timing with the real-verify path
        await store.record_failure(email)
        raise _INVALID_CREDENTIALS

    valid, needs_rehash = security.verify_password(body.password, user.password_hash)
    if not valid:
        await store.record_failure(email)
        raise _INVALID_CREDENTIALS
    if needs_rehash:  # legacy bcrypt (or outdated Argon2 params) → Argon2id
        user.password_hash = security.hash_password(body.password)
        await session.commit()

    await store.clear_failures(email)

    if user.mfa_enabled:
        return MFARequiredResponse(mfa_token=issuer.issue_mfa(user.id))
    return await _issue_tokens(issuer, store, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> TokenResponse:
    try:
        claims = issuer.decode(body.refresh_token, "refresh")
        ctx = issuer.auth_context(claims)
        family = str(claims["fam"])
    except (TokenError, KeyError) as exc:
        raise _INVALID_CREDENTIALS from exc

    new_refresh = issuer.issue_refresh(ctx.user_id, ctx.org_id, ctx.role, family)
    outcome = await store.rotate(family, body.refresh_token, new_refresh)
    if outcome != 1:
        # 0 = expired/unknown; -1 = reuse detected and family already revoked.
        raise _INVALID_CREDENTIALS
    return TokenResponse(
        access_token=issuer.issue_access(ctx.user_id, ctx.org_id, ctx.role),
        refresh_token=new_refresh,
        expires_in=issuer.access_ttl,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> None:
    try:
        claims = issuer.decode(body.refresh_token, "refresh")
        await store.revoke_family(str(claims.get("fam", "")))
    except TokenError:
        pass  # 204 regardless — logout is not an oracle


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> MFASetupResponse:
    user = await session.get(User, auth.user_id)
    if user is None or not user.is_active:
        raise _INVALID_CREDENTIALS
    secret = security.new_totp_secret()
    keys = get_key_material(settings)
    user.totp_secret_enc = security.encrypt_totp_secret(keys.totp_enc_key, secret)
    user.mfa_enabled = False  # armed only after /mfa/verify confirms a code
    await session.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=settings.rp_name)
    return MFASetupResponse(secret=secret, otpauth_uri=uri)


@router.post("/mfa/verify", response_model=TokenResponse)
async def mfa_verify(
    body: MFAVerifyRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    maybe_auth: Annotated[AuthContext | None, Depends(get_optional_auth)],
) -> TokenResponse:
    # Two modes: mfa_token present → completing a login; otherwise an
    # authenticated user is confirming their fresh /mfa/setup secret.
    if body.mfa_token is not None:
        try:
            claims = issuer.decode(body.mfa_token, "mfa")
            user_id = uuid.UUID(str(claims["sub"]))
        except (TokenError, KeyError, ValueError) as exc:
            raise _INVALID_CREDENTIALS from exc
    elif maybe_auth is not None:
        user_id = maybe_auth.user_id
    else:
        raise _INVALID_CREDENTIALS

    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.totp_secret_enc is None:
        raise _INVALID_CREDENTIALS

    keys = get_key_material(settings)
    secret = security.decrypt_totp_secret(keys.totp_enc_key, user.totp_secret_enc)
    if not pyotp.TOTP(secret).verify(body.code, valid_window=1):
        raise _INVALID_CREDENTIALS

    if not user.mfa_enabled:  # first successful verify arms MFA
        user.mfa_enabled = True
        await session.commit()
    return await _issue_tokens(issuer, store, user)
