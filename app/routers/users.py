"""GDPR endpoints: Art. 15 export, Art. 17 erasure (anonymization)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_auth, get_session_store
from app.core.security import AuthContext, SessionStore
from app.db import get_session
from app.services import gdpr_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/export")
async def export_me(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        return await gdpr_service.export_user_data(session, auth.user_id)
    except gdpr_service.UserNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found") from exc


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    auth: Annotated[AuthContext, Depends(get_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> None:
    try:
        await gdpr_service.anonymize_user(session, store, auth.user_id)
    except gdpr_service.UserNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found") from exc
