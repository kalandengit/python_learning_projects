"""Authentication: tenant bootstrap, invitations, login, password reset."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import (
    CurrentUser,
    client_ip,
    enforce_rate_limit,
    login_limiter,
    require_roles,
)
from ..models import (
    AuthToken,
    AuthTokenKind,
    Tenant,
    User,
    UserRole,
    UserStatus,
)
from ..models.base import ensure_aware, utcnow
from ..schemas.auth import (
    AcceptInvite,
    InviteCreate,
    InviteResult,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResult,
    TokenResponse,
    UserOut,
)
from ..schemas.common import TenantCreate, TenantOut
from ..security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from ..services.audit import record_audit

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(db: Session, user: User, kind: AuthTokenKind, ttl_hours: int) -> str:
    raw = generate_opaque_token()
    db.add(
        AuthToken(
            user_id=user.id,
            kind=kind,
            token_hash=hash_token(raw),
            expires_at=utcnow() + timedelta(hours=ttl_hours),
        )
    )
    return raw


@router.post("/bootstrap-tenant", response_model=TenantOut, status_code=201)
def bootstrap_tenant(payload: TenantCreate, db: Session = Depends(get_db)) -> Tenant:
    """Create a tenant. Platform-admin operation; open here for setup/dev."""
    if db.scalar(select(Tenant).where(Tenant.slug == payload.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already in use")
    tenant = Tenant(name=payload.name, slug=payload.slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/tenants/{tenant_id}/first-admin", response_model=InviteResult, status_code=201)
def create_first_admin(
    tenant_id: str, payload: InviteCreate, db: Session = Depends(get_db)
) -> InviteResult:
    """Seed the very first admin for a tenant. Allowed only while the tenant has
    no users, closing the bootstrap gap without leaving the endpoint open."""
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    if db.scalar(select(User).where(User.tenant_id == tenant_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tenant already has users")

    user = User(
        tenant_id=tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        role=UserRole.ADMIN,
        status=UserStatus.INVITED,
    )
    db.add(user)
    db.flush()
    raw = _issue_token(db, user, AuthTokenKind.INVITE, settings.invite_token_ttl_hours)
    record_audit(
        db,
        tenant_id=tenant_id,
        action="user.first_admin",
        actor_id=user.id,
        target_type="user",
        target_id=user.id,
    )
    db.commit()
    return InviteResult(user_id=user.id, email=payload.email, invite_token=raw)


@router.post("/tenants/{tenant_id}/invite", response_model=InviteResult, status_code=201)
def invite_user(
    tenant_id: str,
    payload: InviteCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_roles(UserRole.ADMIN)),
) -> InviteResult:
    if admin.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-tenant invite denied")

    existing = db.scalar(
        select(User).where(User.tenant_id == tenant_id, User.email == payload.email)
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")

    user = User(
        tenant_id=tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        status=UserStatus.INVITED,
    )
    db.add(user)
    db.flush()

    raw = _issue_token(db, user, AuthTokenKind.INVITE, settings.invite_token_ttl_hours)
    record_audit(
        db,
        tenant_id=tenant_id,
        action="user.invite",
        actor_id=admin.id,
        target_type="user",
        target_id=user.id,
        ip=client_ip(request),
        after_state={"email": payload.email, "role": payload.role.value},
    )
    db.commit()
    return InviteResult(user_id=user.id, email=payload.email, invite_token=raw)


@router.post("/accept-invite", response_model=UserOut)
def accept_invite(payload: AcceptInvite, db: Session = Depends(get_db)) -> User:
    token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(payload.token),
            AuthToken.kind == AuthTokenKind.INVITE,
        )
    )
    if not token or token.used_at is not None or ensure_aware(token.expires_at) < utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired invite")

    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid invite")

    user.hashed_password = hash_password(payload.password)
    user.status = UserStatus.ACTIVE
    user.must_reset_password = False
    if payload.full_name:
        user.full_name = payload.full_name
    token.used_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    enforce_rate_limit(
        login_limiter, f"login:{payload.email}", settings.rate_limit_login
    )
    user = db.scalar(select(User).where(User.email == payload.email))
    # Uniform error to avoid leaking which emails exist.
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if (
        user is None
        or user.is_deleted
        or user.status != UserStatus.ACTIVE
        or not user.hashed_password
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise invalid

    record_audit(
        db,
        tenant_id=user.tenant_id,
        action="user.login",
        actor_id=user.id,
        ip=client_ip(request),
    )
    db.commit()
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    return TokenResponse(access_token=token, must_reset_password=user.must_reset_password)


@router.post("/reset/request", response_model=PasswordResetResult)
def request_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or user.is_deleted:
        # Do not reveal absence of the account; return a decoy token.
        return PasswordResetResult(reset_token=generate_opaque_token())
    raw = _issue_token(db, user, AuthTokenKind.RESET, settings.reset_token_ttl_hours)
    db.commit()
    return PasswordResetResult(reset_token=raw)


@router.post("/reset/confirm", response_model=UserOut)
def confirm_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> User:
    token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(payload.token),
            AuthToken.kind == AuthTokenKind.RESET,
        )
    )
    if not token or token.used_at is not None or ensure_aware(token.expires_at) < utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reset token")

    user.hashed_password = hash_password(payload.password)
    user.must_reset_password = False
    if user.status == UserStatus.INVITED:
        user.status = UserStatus.ACTIVE
    token.used_at = utcnow()
    db.commit()
    db.refresh(user)
    return user
