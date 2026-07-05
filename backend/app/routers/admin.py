"""Tenant administration: feature flags, audit-log query and retention purge."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import CurrentUser, require_roles
from ..models import AuditLog, FeatureFlag, UserRole
from ..schemas.common import (
    AuditLogOut,
    FeatureFlagIn,
    FeatureFlagOut,
    PurgeResult,
)
from ..services.purge import purge_expired

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_roles(UserRole.ADMIN)
# Audit logs are readable by admins and HR (for compliance investigations).
_admin_or_hr = require_roles(UserRole.ADMIN, UserRole.HR)


@router.get("/feature-flags", response_model=list[FeatureFlagOut])
def list_flags(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(_admin),
) -> list[FeatureFlag]:
    return list(
        db.scalars(select(FeatureFlag).where(FeatureFlag.tenant_id == admin.tenant_id))
    )


@router.put("/feature-flags", response_model=FeatureFlagOut)
def upsert_flag(
    payload: FeatureFlagIn,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(_admin),
) -> FeatureFlag:
    flag = db.scalar(
        select(FeatureFlag).where(
            FeatureFlag.tenant_id == admin.tenant_id, FeatureFlag.key == payload.key
        )
    )
    if flag is None:
        flag = FeatureFlag(tenant_id=admin.tenant_id, key=payload.key, enabled=payload.enabled)
        db.add(flag)
    else:
        flag.enabled = payload.enabled
    db.commit()
    db.refresh(flag)
    return flag


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    caller: CurrentUser = Depends(_admin_or_hr),
) -> list[AuditLog]:
    """Query the tenant's audit trail with optional filters and pagination."""
    stmt = select(AuditLog).where(AuditLog.tenant_id == caller.tenant_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)
    if target_id:
        stmt = stmt.where(AuditLog.target_id == target_id)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("/purge", response_model=PurgeResult)
def run_retention_purge(
    retention_days: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(_admin),
) -> PurgeResult:
    """Hard-delete this tenant's soft-deleted rows older than the retention
    window. Defaults to the configured retention period."""
    days = retention_days if retention_days is not None else settings.soft_delete_retention_days
    counts = purge_expired(db, admin.tenant_id, days)
    db.commit()
    return PurgeResult(purged=counts, retention_days=days)
