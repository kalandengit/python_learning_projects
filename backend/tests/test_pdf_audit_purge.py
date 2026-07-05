from datetime import datetime, timedelta, timezone

from app.models import Shift
from app.models.base import utcnow
from tests.conftest import make_user


def _shift(client, planner_token, auth_header, user_id, published=True):
    start = datetime.now(timezone.utc) + timedelta(days=1)
    return client.post(
        "/planning/shifts",
        json={
            "user_id": user_id,
            "title": "Morning",
            "location": "HQ",
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=8)).isoformat(),
            "published": published,
        },
        headers=auth_header(planner_token),
    ).json()


def _emp_id(client, employee_token, auth_header):
    return client.post(
        "/requests", json={"type": "leave"}, headers=auth_header(employee_token)
    ).json()["user_id"]


# --- PDF export -----------------------------------------------------------

def test_planner_pdf_export(client, planner_token, employee_token, auth_header):
    emp_id = _emp_id(client, employee_token, auth_header)
    _shift(client, planner_token, auth_header, emp_id)
    r = client.get("/planning/shifts/export.pdf", headers=auth_header(planner_token))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"
    assert "attachment" in r.headers.get("content-disposition", "")


def test_employee_self_schedule_pdf(client, planner_token, employee_token, auth_header):
    emp_id = _emp_id(client, employee_token, auth_header)
    _shift(client, planner_token, auth_header, emp_id)
    r = client.get("/planning/my-schedule.pdf", headers=auth_header(employee_token))
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


def test_employee_cannot_use_planner_export(client, employee_token, auth_header):
    r = client.get("/planning/shifts/export.pdf", headers=auth_header(employee_token))
    assert r.status_code == 403


def test_pdf_export_with_no_shifts(client, planner_token, auth_header):
    r = client.get("/planning/shifts/export.pdf", headers=auth_header(planner_token))
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


# --- Audit logs -----------------------------------------------------------

def test_audit_logs_readable_by_admin(client, admin_token, employee_token, planner_token, auth_header):
    # employee_token / planner_token fixtures generated invite + login audit rows.
    r = client.get("/admin/audit-logs", headers=auth_header(admin_token))
    assert r.status_code == 200
    actions = {e["action"] for e in r.json()}
    assert "user.login" in actions
    assert "user.invite" in actions


def test_audit_logs_filter_by_action(client, admin_token, employee_token, auth_header):
    r = client.get(
        "/admin/audit-logs?action=user.login", headers=auth_header(admin_token)
    )
    assert r.status_code == 200
    assert all(e["action"] == "user.login" for e in r.json())


def test_audit_logs_pagination(client, admin_token, employee_token, auth_header):
    r = client.get("/admin/audit-logs?limit=1", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_audit_logs_hr_allowed_employee_denied(
    client, tenant, admin_token, employee_token, auth_header
):
    hr = make_user(client, tenant["id"], admin_token, "hr@acme.io", "hr")
    assert client.get("/admin/audit-logs", headers=auth_header(hr)).status_code == 200
    assert client.get("/admin/audit-logs", headers=auth_header(employee_token)).status_code == 403


def test_audit_transition_records_before_after(
    client, employee_token, planner_token, admin_token, auth_header
):
    req = client.post(
        "/requests", json={"type": "leave", "title": "x"}, headers=auth_header(employee_token)
    ).json()
    client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "submitted"},
        headers=auth_header(employee_token),
    )
    r = client.get(
        "/admin/audit-logs?action=request.transition", headers=auth_header(admin_token)
    )
    entry = r.json()[0]
    assert entry["before_state"] == {"state": "draft"}
    assert entry["after_state"] == {"state": "submitted"}


# --- Retention purge ------------------------------------------------------

def test_purge_removes_expired_soft_deleted(
    client, db, planner_token, employee_token, admin_token, auth_header
):
    emp_id = _emp_id(client, employee_token, auth_header)
    shift = _shift(client, planner_token, auth_header, emp_id)
    # Soft delete it.
    client.post(
        "/planning/shifts/bulk",
        json={"shift_ids": [shift["id"]], "action": "delete"},
        headers=auth_header(planner_token),
    )
    # Backdate the deletion beyond the retention window.
    row = db.get(Shift, shift["id"])
    row.deleted_at = utcnow() - timedelta(days=400)
    db.commit()

    r = client.post("/admin/purge?retention_days=90", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["purged"]["shifts"] == 1
    # Row is gone from the database entirely.
    db.expire_all()
    assert db.get(Shift, shift["id"]) is None


def test_purge_keeps_recent_soft_deleted(
    client, planner_token, employee_token, admin_token, auth_header
):
    emp_id = _emp_id(client, employee_token, auth_header)
    shift = _shift(client, planner_token, auth_header, emp_id)
    client.post(
        "/planning/shifts/bulk",
        json={"shift_ids": [shift["id"]], "action": "delete"},
        headers=auth_header(planner_token),
    )
    # Recently deleted → within retention → not purged.
    r = client.post("/admin/purge?retention_days=90", headers=auth_header(admin_token))
    assert r.json()["purged"]["shifts"] == 0


def test_purge_requires_admin(client, planner_token, auth_header):
    r = client.post("/admin/purge", headers=auth_header(planner_token))
    assert r.status_code == 403
