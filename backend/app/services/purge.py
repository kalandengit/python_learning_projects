"""Retention-based hard purge of soft-deleted rows.

Soft delete hides rows immediately (``deleted_at``); this job permanently
removes those whose deletion is older than the retention window. In production
it runs on a schedule; it is also exposed as an admin endpoint for on-demand
runs and is unit-testable.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..models import Attachment, Request, Shift, User
from ..models.base import ensure_aware, utcnow

# Soft-deletable, tenant-scoped models eligible for purge.
_PURGEABLE = (Request, Shift, Attachment, User)


def purge_expired(db: Session, tenant_id: str, retention_days: int) -> dict[str, int]:
    """Hard-delete rows in ``tenant_id`` soft-deleted before the retention cutoff.

    Returns a per-table count of removed rows. Caller commits.
    """
    cutoff = utcnow() - timedelta(days=retention_days)
    counts: dict[str, int] = {}
    for model in _PURGEABLE:
        # Fetch candidates so tz-naive (SQLite) timestamps are normalised before
        # comparison, then delete by id.
        candidates = [
            row
            for row in db.query(model).filter(
                model.tenant_id == tenant_id, model.deleted_at.is_not(None)
            )
            if ensure_aware(row.deleted_at) is not None
            and ensure_aware(row.deleted_at) < cutoff
        ]
        ids = [row.id for row in candidates]
        if ids:
            db.execute(delete(model).where(model.id.in_(ids)))
        counts[model.__tablename__] = len(ids)
    return counts
