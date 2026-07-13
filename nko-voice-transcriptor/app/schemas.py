"""Pydantic request/response schemas (API contract)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def password_not_trivial(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must mix letters and digits/symbols")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - field name, not a secret
    expires_in_minutes: int


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptionOut(BaseModel):
    id: int
    text_latin: str
    text_nko: str
    engine: str
    language: str
    audio_format: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptionUpdate(BaseModel):
    """User edit of a saved transcription's N'Ko text."""

    text_nko: str = Field(min_length=0, max_length=20_000)


class TransliterateIn(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class TransliterateOut(BaseModel):
    text_latin: str
    text_nko: str


class LanguageOut(BaseModel):
    code: str
    name: str
    default: bool


class HealthOut(BaseModel):
    status: str
    version: str
    asr_engine: str
