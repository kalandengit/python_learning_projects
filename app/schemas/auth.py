"""Auth request/response models. Responses never leak whether an account exists."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    full_name: str | None = Field(default=None, max_length=200)
    # Provided → a new organization is created and the user becomes its
    # EVENT_ORGANIZER; omitted → the user joins the public org as ATTENDEE.
    organization_name: str | None = Field(default=None, min_length=2, max_length=200)
    marketing_consent: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class MFARequiredResponse(BaseModel):
    mfa_required: Literal[True] = True
    mfa_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MFASetupResponse(BaseModel):
    secret: str  # shown exactly once; stored encrypted at rest
    otpauth_uri: str


class MFAVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)
    # Present → completes a login (issued by POST /auth/login);
    # absent → confirms enabling MFA for the authenticated user.
    mfa_token: str | None = None
