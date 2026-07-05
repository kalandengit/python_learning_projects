"""Request state-machine transitions with validation, history and audit."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import (
    ALLOWED_TRANSITIONS,
    Notification,
    Request,
    RequestState,
    RequestStatusHistory,
)
from .audit import record_audit


class TransitionError(Exception):
    """Raised when a request state change is not permitted."""


def can_transition(current: RequestState, target: RequestState) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition_request(
    db: Session,
    request: Request,
    target: RequestState,
    *,
    actor_id: str,
    note: str | None = None,
    ip: str | None = None,
    device: str | None = None,
) -> Request:
    """Move ``request`` to ``target`` if allowed, recording history + audit and
    notifying the requester. Raises :class:`TransitionError` otherwise."""
    current = request.state
    if not can_transition(current, target):
        raise TransitionError(f"Cannot transition from {current.value} to {target.value}")

    before = {"state": current.value}
    request.state = target

    db.add(
        RequestStatusHistory(
            request_id=request.id,
            from_state=current,
            to_state=target,
            actor_id=actor_id,
            note=note,
        )
    )

    record_audit(
        db,
        tenant_id=request.tenant_id,
        action="request.transition",
        actor_id=actor_id,
        target_type="request",
        target_id=request.id,
        ip=ip,
        device=device,
        reason=note,
        before_state=before,
        after_state={"state": target.value},
    )

    # Notify the requester of any state change made by someone else.
    if actor_id != request.user_id:
        db.add(
            Notification(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                title=f"Request {target.value.replace('_', ' ')}",
                body=note or f"Your request is now {target.value.replace('_', ' ')}.",
                deep_link=f"/requests/{request.id}",
            )
        )

    return request
