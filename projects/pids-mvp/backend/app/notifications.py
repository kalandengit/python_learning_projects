"""Notification service — provider-agnostic dispatch.

The service turns an alert into notifications across configured channels. Providers are pluggable
(email/SMS/push/webhook/voice); the MVP ships a ``ConsoleProvider`` that logs, so it runs with no
external accounts. Real providers (Twilio, SMTP, FCM/APNs, signed webhooks) implement the same
interface. Escalation policies, quiet hours, and channel fallback are modeled here (master
prompt §Notifications).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

logger = logging.getLogger("pids.notifications")


@dataclass
class NotificationRequest:
    alert_id: str
    channel: str
    target: str
    subject: str
    body: str
    idempotency_key: str


class NotificationProvider(Protocol):
    channel: str

    def send(self, req: NotificationRequest) -> bool:  # pragma: no cover - interface
        ...


class ConsoleProvider:
    """Default provider — logs the notification. Handy for dev and tests."""

    def __init__(self, channel: str) -> None:
        self.channel = channel

    def send(self, req: NotificationRequest) -> bool:
        logger.info("[%s] -> %s | %s: %s", self.channel, req.target, req.subject, req.body)
        return True


@dataclass
class EscalationPolicy:
    """Ordered channels tried until one succeeds, plus quiet-hours suppression.

    ``quiet_hours`` is an inclusive (start_hour, end_hour) window in which only ``critical``
    alerts are delivered; everything else is deferred/suppressed.
    """

    channels: list[str] = field(default_factory=lambda: ["push", "email"])
    quiet_hours: tuple[int, int] | None = None

    def in_quiet_hours(self, now: datetime) -> bool:
        if not self.quiet_hours:
            return False
        start, end = self.quiet_hours
        h = now.hour
        return start <= h or h < end if start > end else start <= h < end


@dataclass
class NotificationService:
    providers: dict[str, NotificationProvider] = field(default_factory=dict)
    policy: EscalationPolicy = field(default_factory=EscalationPolicy)
    _dispatched_keys: set[str] = field(default_factory=set)

    def register(self, provider: NotificationProvider) -> None:
        self.providers[provider.channel] = provider

    def dispatch(
        self,
        *,
        alert_id: str,
        criticality: str,
        target: str,
        subject: str,
        body: str,
        now: datetime | None = None,
    ) -> list[NotificationRequest]:
        """Deliver an alert per the escalation policy. Returns the notifications attempted.

        - Deduplicates on ``(alert_id, channel)`` so retries don't double-notify.
        - Honors quiet hours except for ``critical`` alerts.
        - Tries channels in order; stops at the first success (fallback chain).
        """
        now = now or datetime.now(timezone.utc)
        sent: list[NotificationRequest] = []

        if self.policy.in_quiet_hours(now) and criticality != "critical":
            logger.info("quiet hours: suppressing %s alert %s", criticality, alert_id)
            return sent

        for channel in self.policy.channels:
            provider = self.providers.get(channel)
            if provider is None:
                continue
            key = f"{alert_id}:{channel}"
            if key in self._dispatched_keys:
                continue
            req = NotificationRequest(
                alert_id=alert_id,
                channel=channel,
                target=target,
                subject=subject,
                body=body,
                idempotency_key=key,
            )
            ok = provider.send(req)
            self._dispatched_keys.add(key)
            sent.append(req)
            if ok:
                break  # fallback chain: first success wins
        return sent


def default_service() -> NotificationService:
    svc = NotificationService()
    for channel in ("push", "email", "sms", "webhook"):
        svc.register(ConsoleProvider(channel))
    return svc
