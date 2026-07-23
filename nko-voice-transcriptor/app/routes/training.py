"""Protected review and dataset export endpoints."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import TrainingSample
from app.schemas import TrainingReview, TrainingSampleOut

router = APIRouter(prefix="/api/training", tags=["training"])


def require_reviewer(
    x_review_key: str = Header(default=""), settings: Settings = Depends(get_settings)
) -> None:
    if not settings.review_api_key or x_review_key != settings.review_api_key:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Reviewer access required")


@router.get("/samples", response_model=list[TrainingSampleOut])
def list_samples(
    sample_status: str = Query(default="pending", alias="status"),
    _: None = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    stmt = select(TrainingSample).order_by(TrainingSample.created_at.asc()).limit(500)
    if sample_status != "all":
        stmt = stmt.where(TrainingSample.status == sample_status)
    return list(db.scalars(stmt))


@router.patch("/samples/{sample_id}", response_model=TrainingSampleOut)
def review_sample(
    sample_id: int,
    body: TrainingReview,
    _: None = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    row = db.get(TrainingSample, sample_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sample not found")
    row.status = body.status
    row.reviewer_note = body.reviewer_note
    if body.corrected_text_latin is not None:
        row.corrected_text_latin = body.corrected_text_latin
    if body.corrected_text_nko is not None:
        row.corrected_text_nko = body.corrected_text_nko
    row.reviewed_at = datetime.now(UTC) if body.status != "pending" else None
    db.commit()
    db.refresh(row)
    return row


@router.get("/samples/{sample_id}/audio")
def sample_audio(
    sample_id: int,
    _: None = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    row = db.get(TrainingSample, sample_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sample not found")
    return FileResponse(row.audio_path, media_type="audio/wav", filename=f"sample-{row.id}.wav")


@router.get("/export.csv")
def export_approved(
    _: None = Depends(require_reviewer), db: Session = Depends(get_db)
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["file_name", "transcription", "language", "sample_id"])
    rows = db.scalars(
        select(TrainingSample).where(
            TrainingSample.status == "approved", TrainingSample.consent.is_(True)
        )
    )
    for row in rows:
        writer.writerow(
            [f"audio/{row.id}.wav", row.corrected_text_latin, row.language, row.id]
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nko-approved-dataset.csv"},
    )
