"""Per-user transcription history."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TrainingSample, Transcription, TranscriptSegment, User
from app.schemas import SegmentOut, SegmentUpdate, TranscriptionOut, TranscriptionUpdate
from app.security import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


def _stamp(milliseconds: int, separator: str = ",") -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{millis:03}"


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


@router.get("/export.csv")
def export_history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "language", "engine", "text_latin", "text_nko"])
    for row in db.scalars(
        select(Transcription)
        .where(Transcription.user_id == user.id)
        .order_by(Transcription.created_at.asc())
    ):
        writer.writerow(
            [
                row.id,
                row.created_at.isoformat(),
                row.language,
                row.engine,
                row.text_latin,
                row.text_nko,
            ]
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nko-history.csv"},
    )


@router.get("/{transcription_id}/segments", response_model=list[SegmentOut])
def list_segments(
    transcription_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_or_404(transcription_id, user, db)
    return list(
        db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcription_id == transcription_id)
            .order_by(TranscriptSegment.position.asc())
        )
    )


@router.patch("/{transcription_id}/segments/{segment_id}", response_model=SegmentOut)
def edit_segment(
    transcription_id: int,
    segment_id: int,
    body: SegmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_or_404(transcription_id, user, db)
    segment = db.get(TranscriptSegment, segment_id)
    if segment is None or segment.transcription_id != transcription_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Segment not found")
    segment.text_latin = body.text_latin
    segment.text_nko = body.text_nko
    db.commit()
    db.refresh(segment)
    return segment


@router.get("/{transcription_id}/subtitles")
def download_subtitles(
    transcription_id: int,
    format: str = Query(default="vtt", pattern=r"^(vtt|srt)$"),
    script: str = Query(default="nko", pattern=r"^(nko|latin)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_or_404(transcription_id, user, db)
    segments = list(
        db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcription_id == transcription_id)
            .order_by(TranscriptSegment.position.asc())
        )
    )
    lines = ["WEBVTT", ""] if format == "vtt" else []
    for index, segment in enumerate(segments, 1):
        if format == "srt":
            lines.append(str(index))
        separator = "." if format == "vtt" else ","
        lines.append(
            f"{_stamp(segment.start_ms, separator)} --> {_stamp(segment.end_ms, separator)}"
        )
        lines.append(segment.text_nko if script == "nko" else segment.text_latin)
        lines.append("")
    media = "text/vtt" if format == "vtt" else "application/x-subrip"
    return Response(
        "\n".join(lines),
        media_type=f"{media}; charset=utf-8",
        headers={"Content-Disposition": (
            f"attachment; filename=transcription-{transcription_id}-{script}.{format}"
        )},
    )


@router.delete("", status_code=status.HTTP_200_OK)
def clear_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Delete all of the caller's transcriptions. Scoped to the owner only."""
    samples = list(
        db.scalars(select(TrainingSample).where(TrainingSample.user_id == user.id))
    )
    for sample in samples:
        Path(sample.audio_path).unlink(missing_ok=True)
        db.delete(sample)
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
    if body.text_latin is not None:
        row.text_latin = body.text_latin
    sample = db.scalar(
        select(TrainingSample).where(TrainingSample.transcription_id == transcription_id)
    )
    if sample is not None and body.submit_for_training:
        sample.corrected_text_latin = row.text_latin
        sample.corrected_text_nko = row.text_nko
        sample.status = "pending"
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
    sample = db.scalar(
        select(TrainingSample).where(TrainingSample.transcription_id == transcription_id)
    )
    if sample is not None:
        Path(sample.audio_path).unlink(missing_ok=True)
        db.delete(sample)
    db.delete(row)
    db.commit()
