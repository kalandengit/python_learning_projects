"""Unified chronological employee timeline.

Aggregates shifts, requests and notifications for a single employee into one
sorted stream. (Leave/absence/desiderata are surfaced through their requests;
planner changes appear via request transitions and notifications.)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import CurrentUser, get_current_user
from ..models import Notification
from ..models import Request as RequestModel
from ..models import Shift, UserRole
from ..schemas.common import TimelineEntry

router = APIRouter(prefix="/timeline", tags=["timeline"])

_PLANNER_ROLES = {UserRole.PLANNER, UserRole.ADMIN}


@router.get("/{user_id}", response_model=list[TimelineEntry])
def get_timeline(
    user_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[TimelineEntry]:
    # Employees may only see their own timeline; planners/admins may see any in
    # their tenant.
    if user_id != user.id and user.role not in _PLANNER_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")

    entries: list[TimelineEntry] = []

    shifts = db.scalars(
        select(Shift).where(
            Shift.tenant_id == user.tenant_id,
            Shift.user_id == user_id,
            Shift.deleted_at.is_(None),
        )
    )
    for s in shifts:
        entries.append(
            TimelineEntry(
                kind="shift", id=s.id, title=s.title, at=s.starts_at,
                detail=s.location, deep_link=f"/shifts/{s.id}",
            )
        )

    reqs = db.scalars(
        select(RequestModel).where(
            RequestModel.tenant_id == user.tenant_id,
            RequestModel.user_id == user_id,
            RequestModel.deleted_at.is_(None),
        )
    )
    for r in reqs:
        entries.append(
            TimelineEntry(
                kind="request", id=r.id, title=r.title or r.type.value, at=r.created_at,
                detail=f"{r.type.value} · {r.state.value}", deep_link=f"/requests/{r.id}",
            )
        )

    notes = db.scalars(
        select(Notification).where(
            Notification.tenant_id == user.tenant_id,
            Notification.user_id == user_id,
            Notification.archived_at.is_(None),
        )
    )
    for n in notes:
        entries.append(
            TimelineEntry(
                kind="notification", id=n.id, title=n.title, at=n.created_at,
                detail=n.body, deep_link=n.deep_link,
            )
        )

    entries.sort(key=lambda e: e.at, reverse=True)
    return entries
