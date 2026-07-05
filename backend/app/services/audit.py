"""Audit logging helper."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog


def record_audit(
    db: Session,
    *,
    tenant_id: str,
    action: str,
    actor_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    ip: str | None = None,
    device: str | None = None,
    reason: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
) -> AuditLog:
    """Append an immutable audit entry. Caller is responsible for committing."""
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip=ip,
        device=device,
        reason=reason,
        before_state=before_state,
        after_state=after_state,
    )
    db.add(entry)
    return entry
