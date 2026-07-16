"""Core endpoints: audio → N'Ko transcription, and text-only transliteration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.asr import ASREngine, AudioValidationError
from app.asr.base import read_upload_limited, validate_audio, wav_duration_seconds
from app.config import Settings, get_settings
from app.db import get_db
from app.languages import display_name
from app.limits import limiter
from app.llm import improve_transcript
from app.logging_conf import get_logger
from app.models import Transcription, User
from app.nko import transliterate
from app.schemas import LanguageOut, TranscriptionOut, TransliterateIn, TransliterateOut
from app.security import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["transcription"])


def get_asr_engine(request: Request) -> ASREngine:
    return request.app.state.asr_engine


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(settings: Settings = Depends(get_settings)):
    """Source languages this deployment offers, default first."""
    codes = settings.language_list
    ordered = [settings.default_language] + [c for c in codes if c != settings.default_language]
    return [
        LanguageOut(code=c, name=display_name(c), default=(c == settings.default_language))
        for c in ordered
    ]


@router.post("/transcribe", response_model=TranscriptionOut)
@limiter.limit("30/minute")
async def transcribe_audio(
    request: Request,
    audio: UploadFile,
    language: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: ASREngine = Depends(get_asr_engine),
):
    lang = language or settings.default_language
    if lang not in settings.language_list:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unsupported language {lang!r}; offered: {', '.join(settings.language_list)}",
        )
    try:
        data = await read_upload_limited(audio, settings.max_upload_bytes)
        audio_format = validate_audio(data, audio.content_type, settings)
        # WAV duration is checkable without ML deps; other containers are
        # enforced inside the MMS decode path.
        duration = wav_duration_seconds(data)
        if duration is not None and duration > settings.max_audio_seconds:
            raise AudioValidationError(
                f"Audio longer than {settings.max_audio_seconds}s limit"
            )
        result = engine.transcribe(data, audio_format, language=lang)
    except AudioValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except RuntimeError as exc:
        # e.g. MMS selected but torch not installed
        logger.error("event=asr_unavailable error=%s", exc)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Speech recognition engine unavailable"
        ) from exc

    text_latin = improve_transcript(result.text_latin, lang, settings)
    text_nko = transliterate(text_latin)
    record = Transcription(
        user_id=user.id,
        text_latin=text_latin,
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
