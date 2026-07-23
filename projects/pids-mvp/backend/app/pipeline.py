"""Detection processing pipeline.

Single place where an incoming detection is turned into (possibly) an alert:

    dedup -> persist event -> rule evaluation -> alert + audit -> notification

In production the stages between "persist event" and "alert" run off a Kafka topic
(``detection.received`` -> ``alert.created``); here they run inline for the MVP so the whole
flow is testable in one process. The seams (dedup backend, rule source, notifier) are injected.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import models
from .config import get_settings
from .dedup import DedupBackend, compute_idempotency_key
from .metrics import record_alert, record_dedup_dropped, record_event, record_notifications
from .notifications import NotificationService
from .rule_engine import RuleEngine, build_context
from .schemas import DetectionEventIn, IngestResult

settings = get_settings()


def _load_rules(db: Session, tenant_id: str) -> list[dict]:
    rows = db.query(models.Rule).filter(models.Rule.tenant_id == tenant_id).all()
    return [
        {
            "name": r.name,
            "priority": r.priority,
            "conditions": r.conditions,
            "action": r.action,
            "enabled": r.enabled,
        }
        for r in rows
    ]


def process_detection(
    db: Session,
    payload: DetectionEventIn,
    *,
    dedup: DedupBackend,
    notifier: NotificationService,
) -> IngestResult:
    camera = db.get(models.Camera, payload.camera_id)
    if camera is None:
        raise ValueError("unknown camera")

    ts = payload.ts or datetime.now(timezone.utc)
    key = compute_idempotency_key(
        camera_id=payload.camera_id,
        object_class=payload.object_class,
        ts_epoch=ts.timestamp(),
        window_seconds=settings.dedup_window_seconds,
        track_id=payload.track_id,
    )

    # 1. Deduplicate (at-least-once safe).
    if dedup.seen(key, settings.dedup_window_seconds):
        record_dedup_dropped()
        return IngestResult(status="duplicate")

    # 2. Persist the event + mark camera alive.
    event = models.Event(
        tenant_id=camera.tenant_id,
        camera_id=camera.id,
        ts=ts,
        object_class=payload.object_class,
        confidence=payload.confidence,
        bbox=payload.bbox,
        track_id=payload.track_id,
        idempotency_key=key,
    )
    camera.status = "online"
    camera.last_seen = ts
    db.add(event)
    db.flush()  # assign event.id

    # 3. Evaluate rules.
    zone_name = camera.zones[0].name if camera.zones else None
    ctx = build_context(
        object_class=payload.object_class,
        confidence=payload.confidence,
        zone=zone_name,
        ts=ts,
    )
    engine = RuleEngine(rules=_load_rules(db, camera.tenant_id))
    outcome = engine.evaluate(ctx)

    db.add(
        models.AuditLog(
            tenant_id=camera.tenant_id,
            actor="rule_engine",
            action="evaluate",
            detail={"event_id": event.id, "decision": outcome.decision, "rule": outcome.matched_rule},
        )
    )

    record_event(outcome.decision)

    if not outcome.is_intrusion():
        db.commit()
        return IngestResult(
            status=outcome.decision,
            event_id=event.id,
            decision=outcome.decision,
            matched_rule=outcome.matched_rule,
        )

    # 4. Create the alert + history + notify.
    alert = models.Alert(
        tenant_id=camera.tenant_id,
        event_id=event.id,
        camera_id=camera.id,
        zone_id=camera.zones[0].id if camera.zones else None,
        type=payload.object_class,
        criticality=outcome.criticality or "medium",
        status="NEW",
    )
    db.add(alert)
    db.flush()
    db.add(
        models.AlertHistory(
            alert_id=alert.id, from_status=None, to_status="NEW", actor="rule_engine", reason=outcome.reason
        )
    )

    for req in notifier.dispatch(
        alert_id=alert.id,
        criticality=alert.criticality,
        target="soc-oncall",
        subject=f"[{alert.criticality.upper()}] {payload.object_class} at {camera.name}",
        body=f"Intrusion detected on camera {camera.name} (rule: {outcome.matched_rule})",
        now=ts,
    ):
        db.add(
            models.Notification(
                alert_id=alert.id,
                channel=req.channel,
                target=req.target,
                status="sent",
                idempotency_key=req.idempotency_key,
                sent_at=datetime.now(timezone.utc),
            )
        )

    db.commit()
    record_alert(alert.criticality)
    record_notifications(len(alert.notifications))
    return IngestResult(
        status="intrusion",
        event_id=event.id,
        alert_id=alert.id,
        decision="intrusion",
        matched_rule=outcome.matched_rule,
    )
