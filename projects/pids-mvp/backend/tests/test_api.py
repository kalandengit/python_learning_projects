"""End-to-end API tests driving the full detection→alert pipeline via TestClient."""
from __future__ import annotations

from datetime import datetime, timezone


def _seed_camera_id(client, auth_headers) -> str:
    cams = client.get("/api/v1/cameras", headers=auth_headers).json()
    assert cams, "seed should have created a camera"
    return cams[0]["id"]


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_login_and_me(client, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "super_admin"


def test_unauthenticated_is_rejected(client):
    assert client.get("/api/v1/cameras").status_code == 401


def test_ingest_human_at_night_creates_alert(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    payload = {
        "camera_id": cam_id,
        "object_class": "human",
        "confidence": 0.95,
        "ts": datetime(2026, 7, 5, 23, 30, tzinfo=timezone.utc).isoformat(),
    }
    resp = client.post("/api/v1/events", json=payload)
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "intrusion"
    assert body["alert_id"]

    alerts = client.get("/api/v1/alerts", headers=auth_headers).json()
    assert any(a["id"] == body["alert_id"] and a["criticality"] == "high" for a in alerts)


def test_duplicate_event_is_deduped(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    payload = {
        "camera_id": cam_id,
        "object_class": "human",
        "confidence": 0.9,
        "ts": datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "track_id": "t-42",
    }
    first = client.post("/api/v1/events", json=payload).json()
    second = client.post("/api/v1/events", json=payload).json()
    assert first["status"] == "intrusion"
    assert second["status"] == "duplicate"


def test_dog_is_ignored_no_alert(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    resp = client.post(
        "/api/v1/events",
        json={"camera_id": cam_id, "object_class": "dog", "confidence": 0.99},
    )
    assert resp.json()["status"] == "ignore"


def test_unknown_camera_is_404(client):
    resp = client.post(
        "/api/v1/events",
        json={"camera_id": "does-not-exist", "object_class": "human", "confidence": 0.9},
    )
    assert resp.status_code == 404


def test_alert_status_transition_is_audited(client, auth_headers):
    cam_id = _seed_camera_id(client, auth_headers)
    alert_id = client.post(
        "/api/v1/events",
        json={
            "camera_id": cam_id,
            "object_class": "human",
            "confidence": 0.9,
            "ts": datetime(2026, 7, 6, 23, 0, tzinfo=timezone.utc).isoformat(),
        },
    ).json()["alert_id"]

    resp = client.patch(
        f"/api/v1/alerts/{alert_id}",
        json={"status": "ACKNOWLEDGED", "reason": "operator reviewed"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACKNOWLEDGED"


def test_dashboard_stats(client, auth_headers):
    stats = client.get("/api/v1/dashboard/stats", headers=auth_headers).json()
    assert stats["cameras_total"] >= 1


def test_rule_dry_run(client, auth_headers):
    contexts = [
        {"object_class": "human", "confidence": 0.9, "hour": 23, "is_night": True, "zone": None},
        {"object_class": "dog", "confidence": 0.9, "hour": 23, "is_night": True, "zone": None},
    ]
    resp = client.post("/api/v1/rules/dry-run", json=contexts, headers=auth_headers)
    assert resp.status_code == 200
    decisions = [o["decision"] for o in resp.json()]
    assert decisions == ["intrusion", "ignore"]


def test_create_rule_validates(client, auth_headers):
    bad = {"name": "bad", "action": {"decision": "explode"}}
    resp = client.post("/api/v1/rules", json=bad, headers=auth_headers)
    assert resp.status_code == 422
