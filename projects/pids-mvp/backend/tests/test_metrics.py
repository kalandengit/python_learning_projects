"""Tests for the /metrics endpoint and counters."""
from __future__ import annotations

from datetime import datetime, timezone


def _seed_camera_id(client, auth_headers) -> str:
    return client.get("/api/v1/cameras", headers=auth_headers).json()[0]["id"]


def test_metrics_endpoint_exposes_prometheus_text(client):
    body = client.get("/metrics").text
    assert "# TYPE pids_events_total counter" in body


def test_metrics_increment_on_ingest(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    client.post(
        "/api/v1/events",
        json={
            "camera_id": cam_id,
            "object_class": "human",
            "confidence": 0.95,
            "ts": datetime(2026, 7, 5, 23, 15, tzinfo=timezone.utc).isoformat(),
        },
    )
    body = client.get("/metrics").text
    # An intrusion event and a high-criticality alert should be recorded.
    assert 'pids_events_total{decision="intrusion"}' in body
    assert 'pids_alerts_total{criticality="high"}' in body


def test_metrics_dedup_counter(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    payload = {
        "camera_id": cam_id,
        "object_class": "human",
        "confidence": 0.9,
        "ts": datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "track_id": "dedup-metric",
    }
    client.post("/api/v1/events", json=payload)
    client.post("/api/v1/events", json=payload)  # duplicate
    assert "pids_dedup_dropped_total" in client.get("/metrics").text
