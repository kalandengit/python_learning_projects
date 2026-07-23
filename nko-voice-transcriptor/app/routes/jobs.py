"""Background transcription jobs for mobile and long-running uploads."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import db as db_module
from app.asr import ASREngine, AudioValidationError
from app.asr.base import read_upload_limited, validate_audio, wav_duration_seconds
from app.config import Settings, get_settings
from app.correction import retrieve_correction
from app.db import get_db
from app.llm import improve_transcript
from app.media import normalize_media, segment_wav
from app.models import TrainingSample, Transcription, TranscriptionJob, TranscriptSegment, User
from app.nko import transliterate
from app.routes.transcribe import get_asr_engine
from app.schemas import JobOut, TranscriptionOut
from app.security import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _update(job: TranscriptionJob, progress: int, status: str | None = None) -> None:
    job.progress = progress
    if status:
        job.status = status
    job.updated_at = datetime.now(UTC)


def run_transcription_job(job_id: int, engine: ASREngine, settings: Settings) -> None:
    assert db_module.SessionLocal is not None
    with db_module.SessionLocal() as db:
        job = db.get(TranscriptionJob, job_id)
        if job is None:
            return
        try:
            _update(job, 10, "processing")
            db.commit()
            normalized = Path(job.source_path).read_bytes()
            parts = segment_wav(
                normalized, settings.segment_seconds, settings.silence_threshold_db
            )
            results = []
            for index, part in enumerate(parts, 1):
                results.append(engine.transcribe(part, "wav", language=job.language))
                _update(job, 10 + round(index / len(parts) * 60))
                db.commit()
            raw_text = " ".join(result.text_latin for result in results if result.text_latin)
            retrieved, _ = retrieve_correction(raw_text, job.language, db)
            corrected = improve_transcript(retrieved, job.language, settings)
            nko = transliterate(corrected)
            record = Transcription(
                user_id=job.user_id,
                text_latin=corrected,
                text_nko=nko,
                engine=results[0].engine,
                language=job.language,
                audio_format="wav",
                audio_bytes=len(normalized),
            )
            db.add(record)
            db.flush()
            cursor_ms = 0
            for position, (part, result) in enumerate(zip(parts, results, strict=True)):
                end_ms = cursor_ms + round((wav_duration_seconds(part) or 0) * 1000)
                segment_text, _ = retrieve_correction(result.text_latin, job.language, db)
                db.add(
                    TranscriptSegment(
                        transcription_id=record.id,
                        position=position,
                        start_ms=cursor_ms,
                        end_ms=end_ms,
                        text_latin=segment_text,
                        text_nko=transliterate(segment_text),
                    )
                )
                cursor_ms = end_ms
            if job.training_consent:
                training_dir = Path(settings.training_data_dir).resolve()
                training_dir.mkdir(parents=True, exist_ok=True)
                retained = training_dir / f"{record.id}-{uuid4().hex}.wav"
                retained.write_bytes(normalized)
                db.add(
                    TrainingSample(
                        user_id=job.user_id,
                        transcription_id=record.id,
                        audio_path=str(retained),
                        language=job.language,
                        raw_text_latin=raw_text,
                        corrected_text_latin=corrected,
                        corrected_text_nko=nko,
                        consent=True,
                    )
                )
            job.transcription_id = record.id
            _update(job, 100, "completed")
            db.commit()
        except Exception as exc:  # job errors are reported through status polling
            db.rollback()
            job = db.get(TranscriptionJob, job_id)
            if job:
                job.error = str(exc)[:1000]
                _update(job, job.progress, "failed")
                db.commit()
        finally:
            Path(job.source_path).unlink(missing_ok=True)


@router.post("/transcribe", response_model=JobOut, status_code=202)
async def create_job(
    background: BackgroundTasks,
    audio: UploadFile,
    language: str | None = Form(default=None),
    training_consent: bool = Form(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: ASREngine = Depends(get_asr_engine),
):
    lang = language or settings.default_language
    if lang not in settings.language_list:
        raise HTTPException(422, "Unsupported language")
    try:
        data = await read_upload_limited(audio, settings.max_upload_bytes)
        media_format = validate_audio(data, audio.content_type, settings)
        normalized = normalize_media(data, media_format)
        if (wav_duration_seconds(normalized) or 0) > settings.max_audio_seconds:
            raise AudioValidationError("Audio exceeds duration limit")
    except AudioValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
    directory = Path(settings.job_data_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / f"{uuid4().hex}.wav"
    source.write_bytes(normalized)
    job = TranscriptionJob(
        user_id=user.id,
        status="queued",
        progress=0,
        provider=engine.name,
        language=lang,
        source_path=str(source),
        training_consent=training_consent,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    background.add_task(run_transcription_job, job.id, engine, settings)
    return job


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.get(TranscriptionJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/{job_id}/result", response_model=TranscriptionOut)
def job_result(
    job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.get(TranscriptionJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    if job.status != "completed" or job.transcription_id is None:
        raise HTTPException(409, "Job is not complete")
    return db.get(Transcription, job.transcription_id)
