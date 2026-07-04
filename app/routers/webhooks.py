"""Stripe webhooks — raw body, HMAC signature verified before any parsing (§2)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

import stripe as stripe_lib
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_stripe
from app.db import get_session
from app.services import ticket_service
from app.services.stripe_service import StripeConfigError, StripeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    stripe: Annotated[StripeService, Depends(get_stripe)],
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict[str, bool]:
    if stripe_signature is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Missing signature")
    payload = await request.body()
    try:
        event = stripe.construct_webhook_event(payload, stripe_signature)
    except (stripe_lib.SignatureVerificationError, ValueError, StripeConfigError) as exc:
        # Generic rejection — do not explain which check failed.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid payload") from exc

    # StripeObject is not a dict — missing keys raise, so use getattr defaults.
    obj: Any = event["data"]["object"]
    payment_intent = getattr(obj, "payment_intent", None)
    handled = False
    match event["type"]:
        case "checkout.session.completed":
            handled = await ticket_service.fulfill_checkout(
                session,
                checkout_session_id=str(obj["id"]),
                payment_intent_id=str(payment_intent) if payment_intent else None,
            )
        case "checkout.session.expired":
            handled = await ticket_service.release_checkout(
                session, checkout_session_id=str(obj["id"]), reason="checkout_expired"
            )
        case "charge.refunded":
            if payment_intent:
                handled = await ticket_service.refund_payment(
                    session, payment_intent_id=str(payment_intent)
                )
        case _:
            logger.debug("stripe webhook ignored: %s", event["type"])

    return {"received": True, "handled": handled}
