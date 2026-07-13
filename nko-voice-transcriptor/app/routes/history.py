"""Per-user transcription history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Transcription, User
from app.schemas import TranscriptionOut, TranscriptionUpdate
from app.security import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


def _owned_or_404(transcription_id: int, user: User, db: Session) -> Transcription:
    """Fetch a transcription the caller owns, else 404 (IDOR guard)."""
    row = db.get(Transcription, transcription_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return row


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


@router.patch("/{transcription_id}", response_model=TranscriptionOut)
def edit_transcription(
    transcription_id: int,
    body: TranscriptionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a user's manual correction of the generated N'Ko text."""
    row = _owned_or_404(transcription_id, user, db)
    row.text_nko = body.text_nko
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{transcription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcription(
    transcription_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _owned_or_404(transcription_id, user, db)
    db.delete(row)
    db.commit()
