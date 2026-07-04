"""Badges: RBAC issue/toggle + zone-based ABAC validation (§2).

Badges are re-scannable (no single-use transition); every validation is
logged. MANAGEMENT_TEAM is all-access; other types must carry the zone in
their JSONB access_zones. The badge QR envelope uses u = SHA-256(badge id).
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pqc import HybridSigner
from app.core.security import AuthContext
from app.models import Badge, BadgeType, ScanLog, ScanResult, ScanSubject
from app.services.qr_service import QRInvalid, QRService, owner_hash, static_payload


class BadgeError(Exception):
    code = "badge_error"
    http_status = 400


class BadgeNotFound(BadgeError):
    code = "badge_not_found"
    http_status = 404


class BadgeRejected(Exception):
    http_status = 422


@dataclass(frozen=True)
class BadgeValidation:
    badge_id: uuid.UUID
    badge_type: BadgeType
    zone: str | None
    holder_name: str


async def issue_badge(
    session: AsyncSession,
    *,
    actor: AuthContext,
    event_id: uuid.UUID,
    holder_name: str,
    badge_type: BadgeType,
    access_zones: list[str],
    valid_from: datetime,
    valid_until: datetime,
    user_id: uuid.UUID | None,
    nfc_uid: str | None,
    signer: HybridSigner,
) -> Badge:
    token = secrets.token_urlsafe(32)
    badge = Badge(
        organization_id=actor.org_id,
        event_id=event_id,
        user_id=user_id,
        holder_name=holder_name,
        type=badge_type,
        access_zones=access_zones,
        nfc_uid=nfc_uid,
        valid_from=valid_from,
        valid_until=valid_until,
        is_active=True,
        qr_token=token,
    )
    session.add(badge)
    await session.flush()
    badge.pqc_signature = signer.sign(static_payload(token, event_id, badge.id))
    await session.commit()
    return badge


async def toggle_badge(session: AsyncSession, *, badge_id: uuid.UUID, actor: AuthContext) -> Badge:
    badge = await session.get(Badge, badge_id)
    # IDOR: only the owning organization may toggle.
    if badge is None or badge.organization_id != actor.org_id:
        raise BadgeNotFound
    badge.is_active = not badge.is_active
    await session.commit()
    return badge


async def _log(
    session: AsyncSession,
    *,
    result: ScanResult,
    reason: str | None,
    badge: Badge | None,
    event_id: uuid.UUID | None,
    zone: str | None,
    device_id: str,
    scanner: AuthContext,
) -> None:
    session.add(
        ScanLog(
            subject_type=ScanSubject.BADGE,
            subject_id=badge.id if badge else None,
            event_id=badge.event_id if badge else event_id,
            result=result,
            reason=reason,
            zone=zone,
            device_id=device_id,
            scanned_by=scanner.user_id,
        )
    )
    await session.commit()


async def validate_badge(
    session: AsyncSession,
    *,
    qr_data: str,
    zone: str | None,
    device_id: str,
    scanner: AuthContext,
    qr_service: QRService,
    signer: HybridSigner,
) -> BadgeValidation:
    async def reject(reason: str, badge: Badge | None, event_id: uuid.UUID | None) -> None:
        await _log(
            session,
            result=ScanResult.REJECTED,
            reason=reason,
            badge=badge,
            event_id=event_id,
            zone=zone,
            device_id=device_id,
            scanner=scanner,
        )

    try:
        envelope = qr_service.verify(qr_data)
    except QRInvalid as exc:
        await reject(f"envelope:{exc.reason}", None, None)
        raise BadgeRejected from exc

    badge = await session.scalar(select(Badge).where(Badge.qr_token == envelope.qr_token))
    if (
        badge is None
        or badge.event_id != envelope.event_id
        or owner_hash(badge.id) != envelope.owner_hash
    ):
        await reject("unknown_or_mismatched_badge", badge, envelope.event_id)
        raise BadgeRejected

    payload = static_payload(envelope.qr_token, badge.event_id, badge.id)
    if badge.pqc_signature is None or not signer.verify(payload, badge.pqc_signature):
        await reject("pqc_signature_invalid", badge, badge.event_id)
        raise BadgeRejected

    if not badge.is_active:
        await reject("badge_inactive", badge, badge.event_id)
        raise BadgeRejected

    now = datetime.now(UTC)
    if not badge.valid_from <= now <= badge.valid_until:
        await reject("outside_validity_window", badge, badge.event_id)
        raise BadgeRejected

    # Zone ABAC: MANAGEMENT_TEAM = all-access; everyone else needs the zone.
    if badge.type is not BadgeType.MANAGEMENT_TEAM and (
        zone is None or zone not in badge.access_zones
    ):
        await reject("zone_denied", badge, badge.event_id)
        raise BadgeRejected

    await _log(
        session,
        result=ScanResult.ACCEPTED,
        reason=None,
        badge=badge,
        event_id=badge.event_id,
        zone=zone,
        device_id=device_id,
        scanner=scanner,
    )
    return BadgeValidation(
        badge_id=badge.id, badge_type=badge.type, zone=zone, holder_name=badge.holder_name
    )
