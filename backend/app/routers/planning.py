"""Planning: shift management and bulk planner actions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import CurrentUser, client_ip, require_roles
from ..models import Shift, UserRole
from ..models.base import utcnow
from ..schemas.common import BulkShiftAction, ShiftCreate, ShiftOut
from ..services.audit import record_audit

router = APIRouter(prefix="/planning", tags=["planning"])

_planner = require_roles(UserRole.PLANNER, UserRole.ADMIN)


@router.post("/shifts", response_model=ShiftOut, status_code=201)
def create_shift(
    payload: ShiftCreate,
    db: Session = Depends(get_db),
    planner: CurrentUser = Depends(_planner),
) -> Shift:
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "ends_at must be after starts_at")
    shift = Shift(
        tenant_id=planner.tenant_id,
        user_id=payload.user_id,
        title=payload.title,
        location=payload.location,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        published=payload.published,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/shifts", response_model=list[ShiftOut])
def list_shifts(
    db: Session = Depends(get_db),
    planner: CurrentUser = Depends(_planner),
) -> list[Shift]:
    stmt = select(Shift).where(
        Shift.tenant_id == planner.tenant_id, Shift.deleted_at.is_(None)
    ).order_by(Shift.starts_at)
    return list(db.scalars(stmt))


@router.post("/shifts/bulk", response_model=dict)
def bulk_shift_action(
    payload: BulkShiftAction,
    http_request: Request,
    db: Session = Depends(get_db),
    planner: CurrentUser = Depends(_planner),
) -> dict:
    """Apply publish / archive / delete to many shifts in one call."""
    if payload.action not in {"publish", "archive", "delete"}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown bulk action")

    stmt = select(Shift).where(
        Shift.id.in_(payload.shift_ids),
        Shift.tenant_id == planner.tenant_id,
        Shift.deleted_at.is_(None),
    )
    shifts = list(db.scalars(stmt))
    affected = 0
    for shift in shifts:
        if payload.action == "publish":
            shift.published = True
        elif payload.action == "archive":
            shift.published = False
        elif payload.action == "delete":
            shift.deleted_at = utcnow()
            shift.deleted_by = planner.id
        affected += 1

    record_audit(
        db,
        tenant_id=planner.tenant_id,
        action=f"shift.bulk_{payload.action}",
        actor_id=planner.id,
        target_type="shift",
        ip=client_ip(http_request),
        after_state={"ids": [s.id for s in shifts], "count": affected},
    )
    db.commit()
    return {"action": payload.action, "affected": affected}
