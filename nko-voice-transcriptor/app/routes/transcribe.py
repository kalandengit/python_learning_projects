"""Core endpoints: audio → N'Ko transcription, and text-only transliteration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.asr import ASREngine, AudioValidationError
from app.asr.base import validate_audio, wav_duration_seconds
from app.config import Settings, get_settings
from app.db import get_db
from app.limits import limiter
from app.logging_conf import get_logger
from app.models import Transcription, User
from app.nko import transliterate
from app.schemas import TranscriptionOut, TransliterateIn, TransliterateOut
from app.security import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["transcription"])


def get_asr_engine(request: Request) -> ASREngine:
    return request.app.state.asr_engine


@router.post("/transcribe", response_model=TranscriptionOut)
@limiter.limit("30/minute")
async def transcribe_audio(
    request: Request,
    audio: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: ASREngine = Depends(get_asr_engine),
):
    data = await audio.read()
    try:
        audio_format = validate_audio(data, audio.content_type, settings)
        # WAV duration is checkable without ML deps; other containers are
        # enforced inside the MMS decode path.
        duration = wav_duration_seconds(data)
        if duration is not None and duration > settings.max_audio_seconds:
            raise AudioValidationError(
                f"Audio longer than {settings.max_audio_seconds}s limit"
            )
        result = engine.transcribe(data, audio_format)
    except AudioValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except RuntimeError as exc:
        # e.g. MMS selected but torch not installed
        logger.error("event=asr_unavailable error=%s", exc)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Speech recognition engine unavailable"
        ) from exc

    text_nko = transliterate(result.text_latin)
    record = Transcription(
        user_id=user.id,
        text_latin=result.text_latin,
        text_nko=text_nko,
        engine=result.engine,
        language=result.language,
        audio_format=audio_format,
        audio_bytes=len(data),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(
        "event=transcribed user_id=%s engine=%s bytes=%d", user.id, result.engine, len(data)
    )
    return record


@router.post("/transliterate", response_model=TransliterateOut)
@limiter.limit("60/minute")
def transliterate_text(request: Request, body: TransliterateIn):
    """Text-only Latin→N'Ko conversion (no auth needed: stateless, no storage)."""
    return TransliterateOut(text_latin=body.text, text_nko=transliterate(body.text))
