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
