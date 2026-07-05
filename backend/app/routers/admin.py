"""Tenant administration: per-tenant feature flags."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import CurrentUser, require_roles
from ..models import FeatureFlag, UserRole
from ..schemas.common import FeatureFlagIn, FeatureFlagOut

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_roles(UserRole.ADMIN)


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
