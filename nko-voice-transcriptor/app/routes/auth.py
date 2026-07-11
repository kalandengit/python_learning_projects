"""Registration and login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.limits import limiter
from app.logging_conf import get_logger
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(request: Request, body: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == body.username))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("event=user_registered user_id=%s", user.id)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/hour")
def login(request: Request, body: UserCreate, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    # Same error for unknown user and bad password: no username enumeration.
    if user is None or not verify_password(body.password, user.password_hash):
        logger.warning("event=login_failed username_hash=%s", hash(body.username))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in_minutes=settings.access_token_minutes,
    )
