"""ORM models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transcriptions: Mapped[list[Transcription]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transcription(Base):
    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text_latin: Mapped[str] = mapped_column(Text)
    text_nko: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(16))
    language: Mapped[str] = mapped_column(String(8), default="bam")
    audio_format: Mapped[str] = mapped_column(String(8))
    audio_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    user: Mapped[User] = relationship(back_populates="transcriptions")


class TrainingSample(Base):
    """Opt-in audio and corrections; never populated without explicit consent."""

    __tablename__ = "training_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    transcription_id: Mapped[int] = mapped_column(ForeignKey("transcriptions.id"), index=True)
    audio_path: Mapped[str] = mapped_column(String(512))
    language: Mapped[str] = mapped_column(String(8), index=True)
    raw_text_latin: Mapped[str] = mapped_column(Text)
    corrected_text_latin: Mapped[str] = mapped_column(Text, default="")
    corrected_text_nko: Mapped[str] = mapped_column(Text, default="")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    reviewer_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TranscriptionJob(Base):
    __tablename__ = "transcription_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    language: Mapped[str] = mapped_column(String(8), default="bam")
    source_path: Mapped[str] = mapped_column(String(512))
    training_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    transcription_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcriptions.id"), nullable=True
    )
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcription_id: Mapped[int] = mapped_column(ForeignKey("transcriptions.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(32), default="")
    text_latin: Mapped[str] = mapped_column(Text)
    text_nko: Mapped[str] = mapped_column(Text)
