"""Passkeys (WebAuthn): discoverable credentials, UV required, sign_count
clone detection (§2). Challenges live in Valkey with a 5-minute TTL.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from valkey.asyncio import Valkey
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import Settings
from app.core.deps import (
    get_app_settings,
    get_auth,
    get_session_store,
    get_token_issuer,
    get_valkey,
    rate_limit_ip,
)
from app.core.security import AuthContext, SessionStore, TokenIssuer
from app.db import get_session
from app.models import User, WebAuthnCredential
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/passkeys", tags=["passkeys"])

_UNAUTHORIZED = HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


class AuthOptionsResponse(BaseModel):
    challenge_id: str
    options: dict[str, Any]


def _reg_key(user_id: uuid.UUID) -> str:
    return f"webauthn:reg:{user_id}"


def _auth_key(challenge_id: str) -> str:
    return f"webauthn:auth:{challenge_id}"


@router.post("/register/options")
async def register_options(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    valkey: Annotated[Valkey, Depends(get_valkey)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    user = await session.get(User, auth.user_id)
    if user is None or not user.is_active:
        raise _UNAUTHORIZED
    existing = (
        await session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
        )
    ).all()
    options = generate_registration_options(
        rp_id=settings.rp_id,
        rp_name=settings.rp_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.full_name or user.email,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,  # discoverable credentials
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=c.credential_id) for c in existing
        ],
    )
    await valkey.set(
        _reg_key(user.id),
        base64.b64encode(options.challenge).decode(),
        ex=settings.webauthn_challenge_ttl_seconds,
    )
    return json.loads(options_to_json(options))  # type: ignore[no-any-return]


@router.post("/register/verify", status_code=status.HTTP_201_CREATED)
async def register_verify(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    valkey: Annotated[Valkey, Depends(get_valkey)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    credential: Annotated[dict[str, Any], Body()],
) -> dict[str, str]:
    challenge_b64 = await valkey.getdel(_reg_key(auth.user_id))
    if challenge_b64 is None:
        raise _UNAUTHORIZED
    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=base64.b64decode(challenge_b64),
            expected_rp_id=settings.rp_id,
            expected_origin=settings.rp_origin,
            require_user_verification=True,
        )
    except InvalidRegistrationResponse as exc:
        raise _UNAUTHORIZED from exc

    session.add(
        WebAuthnCredential(
            user_id=auth.user_id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=credential.get("response", {}).get("transports"),
            aaguid=str(verification.aaguid) if verification.aaguid else None,
        )
    )
    await session.commit()
    return {"status": "registered"}


@router.post(
    "/login/options",
    response_model=AuthOptionsResponse,
    dependencies=[Depends(rate_limit_ip("passkey_login"))],
)
async def login_options(
    valkey: Annotated[Valkey, Depends(get_valkey)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthOptionsResponse:
    options = generate_authentication_options(
        rp_id=settings.rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenge_id = uuid.uuid4().hex
    await valkey.set(
        _auth_key(challenge_id),
        base64.b64encode(options.challenge).decode(),
        ex=settings.webauthn_challenge_ttl_seconds,
    )
    return AuthOptionsResponse(
        challenge_id=challenge_id, options=json.loads(options_to_json(options))
    )


@router.post(
    "/login/verify",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_ip("passkey_login"))],
)
async def login_verify(
    session: Annotated[AsyncSession, Depends(get_session)],
    valkey: Annotated[Valkey, Depends(get_valkey)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    store: Annotated[SessionStore, Depends(get_session_store)],
    challenge_id: Annotated[str, Body(max_length=64)],
    credential: Annotated[dict[str, Any], Body()],
) -> TokenResponse:
    challenge_b64 = await valkey.getdel(_auth_key(challenge_id))
    if challenge_b64 is None:
        raise _UNAUTHORIZED

    try:
        credential_id = base64url_to_bytes(str(credential["rawId"]))
    except (KeyError, ValueError) as exc:
        raise _UNAUTHORIZED from exc

    stored = await session.scalar(
        select(WebAuthnCredential).where(
            WebAuthnCredential.credential_id == credential_id,
            WebAuthnCredential.is_active.is_(True),
        )
    )
    if stored is None:
        raise _UNAUTHORIZED
    user = await session.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise _UNAUTHORIZED

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=base64.b64decode(challenge_b64),
            expected_rp_id=settings.rp_id,
            expected_origin=settings.rp_origin,
            credential_public_key=stored.public_key,
            credential_current_sign_count=stored.sign_count,
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as exc:
        # Includes sign_count regressions — possible cloned authenticator.
        logger.warning("passkey auth failed for credential %s (possible clone)", stored.id)
        raise _UNAUTHORIZED from exc

    stored.sign_count = verification.new_sign_count
    stored.last_used_at = datetime.now(UTC)
    await session.commit()

    pair = issuer.issue_pair(user.id, user.organization_id, user.role)
    await store.register_family(user.id, pair.family, pair.refresh_token)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=issuer.access_ttl,
    )
