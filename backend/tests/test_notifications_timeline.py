from datetime import datetime, timedelta, timezone


def _emp_id_and_setup(client, employee_token, planner_token, auth_header):
    # Create a request and drive one planner transition to generate a notification.
    r = client.post(
        "/requests", json={"type": "leave", "title": "Trip"}, headers=auth_header(employee_token)
    )
    req = r.json()
    emp_id = req["user_id"]
    client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "submitted"},
        headers=auth_header(employee_token),
    )
    client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "under_review"},
        headers=auth_header(planner_token),
    )
    return emp_id


def test_notification_read_and_archive(client, employee_token, planner_token, auth_header):
    _emp_id_and_setup(client, employee_token, planner_token, auth_header)
    notes = client.get("/notifications", headers=auth_header(employee_token)).json()
    assert len(notes) >= 1
    nid = notes[0]["id"]
    assert notes[0]["is_read"] is False

    r = client.post(f"/notifications/{nid}/read", headers=auth_header(employee_token))
    assert r.json()["is_read"] is True

    r = client.post(f"/notifications/{nid}/archive", headers=auth_header(employee_token))
    assert r.json()["is_archived"] is True

    # Archived hidden by default, visible when requested.
    visible = client.get("/notifications", headers=auth_header(employee_token)).json()
    assert nid not in [n["id"] for n in visible]
    all_notes = client.get(
        "/notifications?include_archived=true", headers=auth_header(employee_token)
    ).json()
    assert nid in [n["id"] for n in all_notes]


def test_timeline_aggregates_kinds(client, employee_token, planner_token, auth_header):
    emp_id = _emp_id_and_setup(client, employee_token, planner_token, auth_header)
    start = datetime.now(timezone.utc) + timedelta(days=2)
    client.post(
        "/planning/shifts",
        json={
            "user_id": emp_id,
            "title": "Late",
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=6)).isoformat(),
            "published": True,
        },
        headers=auth_header(planner_token),
    )
    r = client.get(f"/timeline/{emp_id}", headers=auth_header(employee_token))
    assert r.status_code == 200
    kinds = {e["kind"] for e in r.json()}
    assert {"shift", "request", "notification"} <= kinds


def test_timeline_other_employee_forbidden(
    client, tenant, admin_token, employee_token, auth_header
):
    from tests.conftest import make_user

    other = make_user(client, tenant["id"], admin_token, "other@acme.io", "employee")
    other_req = client.post(
        "/requests", json={"type": "leave"}, headers=auth_header(other)
    ).json()
    r = client.get(f"/timeline/{other_req['user_id']}", headers=auth_header(employee_token))
    assert r.status_code == 403
