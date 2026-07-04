"""Stripe Checkout Sessions + verified webhooks (PCI DSS 4.0.1 SAQ-A).

Card data never touches this server: purchases redirect to Stripe-hosted
Checkout, and fulfilment happens only via signature-verified webhooks.
"""

from __future__ import annotations

import uuid
from typing import cast

import stripe

from app.config import Settings


class StripeConfigError(Exception):
    pass


class StripeService:
    def __init__(
        self,
        *,
        secret_key: str | None,
        webhook_secret: str | None,
        success_url: str,
        cancel_url: str,
    ) -> None:
        self._client = stripe.StripeClient(secret_key) if secret_key else None
        self._webhook_secret = webhook_secret
        self._success_url = success_url
        self._cancel_url = cancel_url

    @classmethod
    def from_settings(cls, settings: Settings) -> StripeService:
        base = settings.frontend_base_url.rstrip("/")
        return cls(
            secret_key=(
                settings.stripe_secret_key.get_secret_value()
                if settings.stripe_secret_key
                else None
            ),
            webhook_secret=(
                settings.stripe_webhook_secret.get_secret_value()
                if settings.stripe_webhook_secret
                else None
            ),
            success_url=f"{base}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/checkout/cancel",
        )

    def _require_client(self) -> stripe.StripeClient:
        if self._client is None:
            raise StripeConfigError("EMS_STRIPE_SECRET_KEY is not configured")
        return self._client

    async def create_checkout_session(
        self,
        *,
        payment_id: uuid.UUID,
        idempotency_key: str,
        product_name: str,
        unit_amount_cents: int,
        currency: str,
        quantity: int,
        customer_email: str,
    ) -> tuple[str, str]:
        """Returns (checkout_session_id, hosted checkout URL)."""
        client = self._require_client()
        checkout = await client.checkout.sessions.create_async(
            params={
                "mode": "payment",
                "client_reference_id": str(payment_id),
                "customer_email": customer_email,
                "line_items": [
                    {
                        "quantity": quantity,
                        "price_data": {
                            "currency": currency,
                            "unit_amount": unit_amount_cents,
                            "product_data": {"name": product_name},
                        },
                    }
                ],
                "metadata": {"payment_id": str(payment_id)},
                "success_url": self._success_url,
                "cancel_url": self._cancel_url,
            },
            options={"idempotency_key": f"checkout:{idempotency_key}"},
        )
        if checkout.url is None:  # pragma: no cover - stripe contract
            raise StripeConfigError("Stripe returned no checkout URL")
        return checkout.id, checkout.url

    async def checkout_url(self, checkout_session_id: str) -> str | None:
        """Re-fetch the hosted URL for idempotent purchase replays."""
        client = self._require_client()
        checkout = await client.checkout.sessions.retrieve_async(checkout_session_id)
        return checkout.url

    async def create_refund(self, *, payment_intent_id: str) -> str:
        client = self._require_client()
        refund = await client.refunds.create_async(
            params={"payment_intent": payment_intent_id},
            options={"idempotency_key": f"refund:{payment_intent_id}"},
        )
        return refund.id

    def construct_webhook_event(self, payload: bytes, signature_header: str) -> stripe.Event:
        """HMAC signature verification — raises on tampered/unsigned payloads."""
        if not self._webhook_secret:
            raise StripeConfigError("EMS_STRIPE_WEBHOOK_SECRET is not configured")
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload, signature_header, self._webhook_secret
        )
        return cast("stripe.Event", event)
