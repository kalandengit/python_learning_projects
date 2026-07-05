"""Employee requests: create/list/get drafts and drive the state machine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import (
    CurrentUser,
    client_ip,
    enforce_rate_limit,
    get_current_user,
    request_limiter,
)
from ..models import Request as RequestModel
from ..models import RequestState, UserRole
from ..schemas.requests import (
    RequestCreate,
    RequestDetail,
    RequestOut,
    RequestUpdate,
    TransitionRequest,
)
from ..services.requests import TransitionError, can_transition, transition_request

settings = get_settings()
router = APIRouter(prefix="/requests", tags=["requests"])

_PLANNER_ROLES = {UserRole.PLANNER, UserRole.ADMIN}


def _load(db: Session, request_id: str, user: CurrentUser) -> RequestModel:
    req = db.get(RequestModel, request_id)
    if req is None or req.is_deleted or req.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    # Owners and planners/admins may view; other employees may not.
    if req.user_id != user.id and user.role not in _PLANNER_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
    return req


@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    payload: RequestCreate,
    http_request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RequestModel:
    enforce_rate_limit(
        request_limiter, f"req:{user.tenant_id}:{user.id}", settings.rate_limit_requests
    )
    req = RequestModel(
        tenant_id=user.tenant_id,
        user_id=user.id,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        state=RequestState.DRAFT,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("", response_model=list[RequestOut])
def list_requests(
    mine: bool = True,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[RequestModel]:
    stmt = select(RequestModel).where(
        RequestModel.tenant_id == user.tenant_id, RequestModel.deleted_at.is_(None)
    )
    if mine or user.role not in _PLANNER_ROLES:
        stmt = stmt.where(RequestModel.user_id == user.id)
    return list(db.scalars(stmt.order_by(RequestModel.created_at.desc())))


@router.get("/{request_id}", response_model=RequestDetail)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RequestModel:
    return _load(db, request_id, user)


@router.patch("/{request_id}", response_model=RequestOut)
def update_request(
    request_id: str,
    payload: RequestUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RequestModel:
    req = _load(db, request_id, user)
    # Content is only editable by the owner while still a draft.
    if req.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner may edit")
    if req.state != RequestState.DRAFT:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only drafts are editable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return req


@router.post("/{request_id}/transition", response_model=RequestDetail)
def do_transition(
    request_id: str,
    payload: TransitionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RequestModel:
    req = _load(db, request_id, user)
    # Validate the transition itself first, so an illegal state jump reads as a
    # 409 regardless of the caller's role; then enforce who may drive it.
    if not can_transition(req.state, payload.target):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot transition from {req.state.value} to {payload.target.value}",
        )
    _authorize_transition(req, payload.target, user)
    try:
        transition_request(
            db,
            req,
            payload.target,
            actor_id=user.id,
            note=payload.note,
            ip=client_ip(http_request),
        )
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    db.commit()
    db.refresh(req)
    return req


# Which party may drive each transition.
_EMPLOYEE_TARGETS = {RequestState.SUBMITTED, RequestState.RESUBMITTED, RequestState.CANCELLED}
_PLANNER_TARGETS = {
    RequestState.UNDER_REVIEW,
    RequestState.NEEDS_INFORMATION,
    RequestState.APPROVED,
    RequestState.REJECTED,
    RequestState.CANCELLED,
}


def _authorize_transition(req: RequestModel, target: RequestState, user: CurrentUser) -> None:
    is_owner = req.user_id == user.id
    is_planner = user.role in _PLANNER_ROLES
    if target in _PLANNER_TARGETS and target != RequestState.CANCELLED and not is_planner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Planner role required")
    if target in _EMPLOYEE_TARGETS and target != RequestState.CANCELLED and not is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner may do this")
    if target == RequestState.CANCELLED and not (is_owner or is_planner):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
