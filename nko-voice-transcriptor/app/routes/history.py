"""Per-user transcription history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Transcription, User
from app.schemas import TranscriptionOut
from app.security import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[TranscriptionOut])
def list_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    rows = db.scalars(
        select(Transcription)
        .where(Transcription.user_id == user.id)
        .order_by(Transcription.created_at.desc(), Transcription.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows)


@router.delete("/{transcription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcription(
    transcription_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Transcription, transcription_id)
    # Ownership check: users can only ever touch their own rows (IDOR guard).
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(row)
    db.commit()
