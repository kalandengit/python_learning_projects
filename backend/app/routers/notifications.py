"""Notification centre: list, mark read/unread, archive."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import CurrentUser, get_current_user
from ..models import Notification
from ..models.base import utcnow
from ..schemas.common import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _load(db: Session, notification_id: str, user: CurrentUser) -> Notification:
    note = db.get(Notification, notification_id)
    if note is None or note.tenant_id != user.tenant_id or note.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return note


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    include_archived: bool = False,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Notification]:
    stmt = select(Notification).where(
        Notification.tenant_id == user.tenant_id, Notification.user_id == user.id
    )
    if not include_archived:
        stmt = stmt.where(Notification.archived_at.is_(None))
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc())))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Notification:
    note = _load(db, notification_id, user)
    if note.read_at is None:
        note.read_at = utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.post("/{notification_id}/archive", response_model=NotificationOut)
def archive(
    notification_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Notification:
    note = _load(db, notification_id, user)
    now = utcnow()
    note.archived_at = now
    if note.read_at is None:
        note.read_at = now
    db.commit()
    db.refresh(note)
    return note
