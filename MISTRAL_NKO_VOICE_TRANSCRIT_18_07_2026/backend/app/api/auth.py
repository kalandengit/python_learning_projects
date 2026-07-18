"""Registration, login (timing-safe), refresh rotation, logout."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.limits import auth_limit, limiter
from app.models import User
from app.security import (
    get_current_user,
    hash_password,
    issue_token_pair,
    revoke_all_tokens,
    rotate_refresh_token,
    verify_password,
)

logger = logging.getLogger("nko.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(auth_limit)
def register(request: Request, body: Credentials, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        # Same status/message shape as success would 409; do not reveal more.
        raise HTTPException(status.HTTP_409_CONFLICT, "Account cannot be created")
    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    logger.info("user_registered user_id=%s", user.id)
    return {"id": user.id, "email": user.email}


@router.post("/login")
@limiter.limit(auth_limit)
def login(request: Request, body: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    # verify_password runs Argon2 even when user is None (dummy hash),
    # keeping login latency independent of account existence.
    ok = verify_password(body.password, user.password_hash if user else None)
    if not ok or user is None:
        logger.info("login_failed")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    logger.info("login_ok user_id=%s", user.id)
    return issue_token_pair(db, user)


@router.post("/refresh")
@limiter.limit(auth_limit)
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db)):
    return rotate_refresh_token(db, body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    revoke_all_tokens(db, user.id)
