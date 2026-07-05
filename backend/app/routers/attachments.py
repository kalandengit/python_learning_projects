"""Request attachments: validated upload, malware-scan gating, HR-only medical."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import (
    CurrentUser,
    enforce_rate_limit,
    get_current_user,
    upload_limiter,
)
from ..models import Attachment, ScanStatus, UserRole
from ..models import Request as RequestModel
from ..schemas.attachments import AttachmentOut
from ..services.storage import scan_blob, store_blob

settings = get_settings()
router = APIRouter(prefix="/requests/{request_id}/attachments", tags=["attachments"])

_PLANNER_ROLES = {UserRole.PLANNER, UserRole.ADMIN}


def _load_request(db: Session, request_id: str, user: CurrentUser) -> RequestModel:
    req = db.get(RequestModel, request_id)
    if req is None or req.is_deleted or req.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return req


@router.post("", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    request_id: str,
    file: UploadFile = File(...),
    is_medical: bool = Form(False),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Attachment:
    enforce_rate_limit(
        upload_limiter, f"upload:{user.tenant_id}:{user.id}", settings.rate_limit_uploads
    )
    req = _load_request(db, request_id, user)
    if req.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner may attach files")

    if file.content_type not in settings.allowed_attachment_types:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Type {file.content_type} not allowed",
        )

    data = await file.read()
    if len(data) > settings.max_attachment_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 10 MB")
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file")

    storage_key = store_blob(file.filename or "upload", data, encrypt=is_medical)
    # Scan gates availability. Here it runs inline; production enqueues it and the
    # attachment stays PENDING (and unavailable) until the scanner reports back.
    verdict = scan_blob(data)

    attachment = Attachment(
        tenant_id=user.tenant_id,
        request_id=req.id,
        uploaded_by=user.id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        size_bytes=len(data),
        storage_key=storage_key,
        scan_status=verdict,
        is_medical=is_medical,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("", response_model=list[AttachmentOut])
def list_attachments(
    request_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Attachment]:
    req = _load_request(db, request_id, user)
    is_owner = req.user_id == user.id
    is_planner = user.role in _PLANNER_ROLES
    if not (is_owner or is_planner):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")

    result: list[Attachment] = []
    for att in _query(db, req.id):
        # Medical documents are restricted to HR (and the uploading owner).
        if att.is_medical and user.role != UserRole.HR and not is_owner:
            continue
        result.append(att)
    return result


def _query(db: Session, request_id: str) -> list[Attachment]:
    return list(
        db.scalars(
            select(Attachment).where(
                Attachment.request_id == request_id, Attachment.deleted_at.is_(None)
            )
        )
    )


@router.get("/{attachment_id}/download")
def download_attachment(
    request_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    req = _load_request(db, request_id, user)
    att = db.get(Attachment, attachment_id)
    if att is None or att.request_id != req.id or att.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")

    is_owner = req.user_id == user.id
    if att.is_medical and user.role != UserRole.HR and not is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Medical document is HR-only")
    if not att.is_available:
        # Not yet scanned clean, or infected/deleted.
        raise HTTPException(status.HTTP_409_CONFLICT, "Attachment not available")

    # Real implementation streams the (decrypted) blob; stub returns the key.
    return {"storage_key": att.storage_key, "filename": att.filename}
