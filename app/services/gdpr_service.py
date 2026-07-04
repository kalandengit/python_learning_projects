"""GDPR: Art. 15 JSON export and Art. 17 anonymization.

Erasure scrubs PII but keeps financial records for the statutory 7-year
retention (amounts + Stripe references contain no card data).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SessionStore
from app.models import Payment, Ticket, User, WebAuthnCredential


class UserNotFound(Exception):
    pass


async def export_user_data(session: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFound
    tickets = (await session.scalars(select(Ticket).where(Ticket.owner_id == user_id))).all()
    payments = (await session.scalars(select(Payment).where(Payment.user_id == user_id))).all()
    credentials = (
        await session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user_id)
        )
    ).all()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "mfa_enabled": user.mfa_enabled,
            "marketing_consent": user.marketing_consent,
            "terms_accepted_at": (
                user.terms_accepted_at.isoformat() if user.terms_accepted_at else None
            ),
            "created_at": user.created_at.isoformat(),
        },
        "webauthn_credentials": [
            {"created_at": c.created_at.isoformat(), "last_used_at": (
                c.last_used_at.isoformat() if c.last_used_at else None
            )}
            for c in credentials
        ],
        "tickets": [
            {
                "id": str(t.id),
                "event_id": str(t.event_id),
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
                "used_at": t.used_at.isoformat() if t.used_at else None,
            }
            for t in tickets
        ],
        "payments": [
            {
                "id": str(p.id),
                "event_id": str(p.event_id),
                "amount_cents": p.amount_cents,
                "currency": p.currency,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
    }


async def anonymize_user(
    session: AsyncSession, store: SessionStore, user_id: uuid.UUID
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFound
    user.email = f"anonymized+{user.id}@erased.invalid"
    user.full_name = None
    user.password_hash = None
    user.totp_secret_enc = None
    user.mfa_enabled = False
    user.marketing_consent = False
    user.is_active = False
    user.anonymized_at = datetime.now(UTC)
    await session.execute(
        delete(WebAuthnCredential).where(WebAuthnCredential.user_id == user_id)
    )
    await session.commit()
    # Kill every live session family for this user.
    await store.revoke_all_for_user(user_id)
