"""Planning: shift management and bulk planner actions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import CurrentUser, client_ip, get_current_user, require_roles
from ..models import Shift, UserRole
from ..models.base import utcnow
from ..schemas.common import BulkShiftAction, ShiftCreate, ShiftOut
from ..services.audit import record_audit
from ..services.pdf import render_schedule_pdf

router = APIRouter(prefix="/planning", tags=["planning"])

_planner = require_roles(UserRole.PLANNER, UserRole.ADMIN)


def _pdf_response(shifts: list[Shift], *, title: str, subtitle: str, filename: str) -> Response:
    body = render_schedule_pdf(shifts, title=title, subtitle=subtitle)
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@router.get("/shifts/export.pdf")
def export_shifts_pdf(
    user_id: str | None = None,
    db: Session = Depends(get_db),
    planner: CurrentUser = Depends(_planner),
) -> Response:
    """Planner PDF export of the tenant's schedule, optionally for one employee."""
    stmt = select(Shift).where(
        Shift.tenant_id == planner.tenant_id, Shift.deleted_at.is_(None)
    )
    if user_id:
        stmt = stmt.where(Shift.user_id == user_id)
    shifts = list(db.scalars(stmt.order_by(Shift.starts_at)))
    subtitle = f"Employee: {user_id}" if user_id else "All employees"
    return _pdf_response(
        shifts, title="StaffHub Schedule", subtitle=subtitle, filename="schedule.pdf"
    )


@router.get("/my-schedule.pdf")
def export_my_schedule_pdf(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    """Any employee may export their own schedule as a PDF."""
    shifts = list(
        db.scalars(
            select(Shift).where(
                Shift.tenant_id == user.tenant_id,
                Shift.user_id == user.id,
                Shift.deleted_at.is_(None),
            ).order_by(Shift.starts_at)
        )
    )
    return _pdf_response(
        shifts, title="My Schedule", subtitle="", filename="my-schedule.pdf"
    )


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
