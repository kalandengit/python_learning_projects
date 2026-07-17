"""Pydantic request/response schemas (API contract)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=10, max_length=128)
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    email: str | None = Field(default=None, min_length=5, max_length=254)

    @field_validator("password")
    @classmethod
    def password_not_trivial(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must mix letters and digits/symbols")
        return v

    @field_validator("email")
    @classmethod
    def email_looks_valid(cls, v: str | None) -> str | None:
        if v is not None and ("@" not in v or "." not in v.rsplit("@", 1)[-1]):
            raise ValueError("Enter a valid email address")
        return v.lower() if v else v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PasswordConfirm(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - field name, not a secret
    expires_in_minutes: int


class RefreshResponse(TokenResponse):
    pass


class UserOut(BaseModel):
    id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
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
    text_latin: str | None = Field(default=None, max_length=20_000)
    submit_for_training: bool = False


class TrainingSampleOut(BaseModel):
    id: int
    transcription_id: int
    language: str
    raw_text_latin: str
    corrected_text_latin: str
    corrected_text_nko: str
    status: str
    reviewer_note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SegmentOut(BaseModel):
    id: int
    position: int
    start_ms: int
    end_ms: int
    speaker: str
    text_latin: str
    text_nko: str

    model_config = {"from_attributes": True}


class SegmentUpdate(BaseModel):
    text_latin: str = Field(max_length=5_000)
    text_nko: str = Field(max_length=5_000)


class JobOut(BaseModel):
    id: int
    status: str
    progress: int
    provider: str
    language: str
    transcription_id: int | None
    error: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrainingReview(BaseModel):
    status: str = Field(pattern=r"^(approved|rejected|pending)$")
    corrected_text_latin: str | None = Field(default=None, max_length=20_000)
    corrected_text_nko: str | None = Field(default=None, max_length=20_000)
    reviewer_note: str = Field(default="", max_length=2_000)


class TransliterateIn(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class TransliterateOut(BaseModel):
    text_latin: str
    text_nko: str


class LanguageOut(BaseModel):
    code: str
    name: str
    default: bool


class AlphabetEntry(BaseModel):
    cp: str
    char: str
    name: str
    latin: str
    kind: str


class DictionaryEntry(BaseModel):
    fr: str
    nko: str
    cat: str = ""


class DictionaryResult(BaseModel):
    query: str
    direction: str
    count: int
    entries: list[DictionaryEntry]


class HealthOut(BaseModel):
    status: str
    version: str
    asr_engine: str
    model_version: str
