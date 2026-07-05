from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from ..models import UserRole


class InviteCreate(BaseModel):
    email: EmailStr
    full_name: str = ""
    role: UserRole = UserRole.EMPLOYEE


class InviteResult(BaseModel):
    user_id: str
    email: EmailStr
    # Raw invite token returned so it can be emailed; never persisted in the clear.
    invite_token: str


class AcceptInvite(BaseModel):
    token: str
    password: str = Field(min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_reset_password: bool = False


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetResult(BaseModel):
    reset_token: str


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: str

    model_config = {"from_attributes": True}
