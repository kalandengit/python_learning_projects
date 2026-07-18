"""Audio upload → ASR → N'Ko, plus authenticated history (IDOR-safe)."""

import logging
import time

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.asr import EngineError, EngineUnavailable, get_engine
from app.config import get_settings
from app.db import get_db
from app.limits import limiter, transcribe_limit
from app.models import Transcript, User
from app.nko import transliterate
from app.security import get_current_user, get_optional_user

logger = logging.getLogger("nko.transcribe")

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])

ALLOWED_MIME = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/ogg", "application/ogg", "audio/opus",
    "audio/flac", "audio/x-flac",
    "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/x-m4a", "audio/aac",
    "audio/webm", "video/webm",
    "application/octet-stream",  # allowed only if magic bytes pass
}

ALLOWED_LANGUAGES = {"bam", "dyu", "mnk", "emk", "jul", "man", "fr", "en"}
ALLOWED_ENGINES = {"mock", "mms", "whisper", "voxtral"}


def sniff_audio(data: bytes) -> str | None:
    """Magic-byte detection; returns a format name or None."""
    if len(data) < 12:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:4] == b"OggS":
        return "ogg"
    if data[:4] == b"fLaC":
        return "flac"
    if data[:3] == b"ID3" or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data[4:8] == b"ftyp":
        return "m4a"
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    return None


@router.post("/upload")
@limiter.limit(transcribe_limit)
async def upload(
    request: Request,
    audio: UploadFile,
    language: str = Form("bam"),
    asr_engine: str | None = Form(None),
    store_history: bool = Form(False),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if language not in ALLOWED_LANGUAGES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported language")
    if asr_engine is not None and asr_engine not in ALLOWED_ENGINES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown ASR engine")
    if audio.content_type not in ALLOWED_MIME:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported media type")

    data = await audio.read()
    settings = get_settings()
    if len(data) > settings.max_upload_bytes:  # middleware enforces this too
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
    if sniff_audio(data) is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Not a recognized audio file")

    engine = get_engine(language, asr_engine)
    started = time.monotonic()
    try:
        latin = engine.transcribe(data, language)
    except EngineUnavailable as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except EngineError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    nko = transliterate(latin)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "transcribed engine=%s language=%s bytes=%d ms=%d",
        engine.name, language, len(data), elapsed_ms,
    )
    # Audio bytes go out of scope here — never written to disk (privacy).

    record_id = None
    if store_history and user is not None:
        record = Transcript(
            user_id=user.id, language=language, engine=engine.name,
            latin_text=latin, nko_text=nko,
        )
        db.add(record)
        db.commit()
        record_id = record.id

    return {
        "id": record_id,
        "latin_text": latin,
        "nko_text": nko,
        "language": language,
        "asr_engine": engine.name,
        "duration_ms": elapsed_ms,
    }


@router.get("")
def list_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    limit = max(1, min(limit, 200))
    rows = db.scalars(
        select(Transcript)
        .where(Transcript.user_id == user.id)  # IDOR protection: own rows only
        .order_by(Transcript.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "language": row.language,
            "asr_engine": row.engine,
            "latin_text": row.latin_text,
            "nko_text": row.nko_text,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def _own_transcript(transcript_id: int, user: User, db: Session) -> Transcript:
    row = db.get(Transcript, transcript_id)
    if row is None or row.user_id != user.id:
        # Cross-user access is indistinguishable from not-found (audit control).
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return row


@router.get("/{transcript_id}")
def get_transcript(
    transcript_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _own_transcript(transcript_id, user, db)
    return {
        "id": row.id,
        "language": row.language,
        "asr_engine": row.engine,
        "latin_text": row.latin_text,
        "nko_text": row.nko_text,
        "created_at": row.created_at.isoformat(),
    }


@router.delete("/{transcript_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript(
    transcript_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _own_transcript(transcript_id, user, db)
    db.delete(row)
    db.commit()
