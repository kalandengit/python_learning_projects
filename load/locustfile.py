"""Locust profile — target: 500 purchases/min sustained (§8).

Run against a compose stack (FREE tier so Stripe is not in the loop):

    EMS_LOAD_TIER_ID=<tier-uuid> uv run locust -f load/locustfile.py \
        --host http://localhost:8000 -u 100 -r 10

Each simulated user registers once, then buys tickets with fresh
Idempotency-Keys and polls its ticket list; ~5:1 read/write mix.
"""

from __future__ import annotations

import os
import uuid

from locust import HttpUser, between, task

TIER_ID = os.environ.get("EMS_LOAD_TIER_ID", "")
PASSWORD = "load-test-password-123!"


class PurchasingAttendee(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        email = f"load-{uuid.uuid4().hex}@load.ems"
        r = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": PASSWORD},
            name="/auth/register",
        )
        r.raise_for_status()
        self._auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    @task(2)
    def purchase(self) -> None:
        if not TIER_ID:
            return
        self.client.post(
            "/api/v1/tickets/purchase",
            json={"tier_id": TIER_ID, "quantity": 1},
            headers={**self._auth, "Idempotency-Key": uuid.uuid4().hex},
            name="/tickets/purchase",
        )

    @task(5)
    def my_tickets(self) -> None:
        self.client.get("/api/v1/tickets/mine", headers=self._auth, name="/tickets/mine")

    @task(3)
    def browse_events(self) -> None:
        self.client.get("/api/v1/events?limit=20", name="/events")
