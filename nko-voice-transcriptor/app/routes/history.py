"""Per-user transcription history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
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
    q: str | None = Query(default=None, max_length=200),
):
    stmt = select(Transcription).where(Transcription.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Transcription.text_nko.ilike(like) | Transcription.text_latin.ilike(like)
        )
    stmt = (
        stmt.order_by(Transcription.created_at.desc(), Transcription.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.get("/count")
def history_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    total = db.scalar(
        select(func.count()).select_from(Transcription).where(Transcription.user_id == user.id)
    )
    return {"count": int(total or 0)}


@router.delete("", status_code=status.HTTP_200_OK)
def clear_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Delete all of the caller's transcriptions. Scoped to the owner only."""
    result = db.execute(delete(Transcription).where(Transcription.user_id == user.id))
    db.commit()
    return {"deleted": int(result.rowcount or 0)}


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
