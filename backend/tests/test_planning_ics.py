from datetime import datetime, timedelta, timezone


def _shift_payload(user_id, **kw):
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        "user_id": user_id,
        "title": "Morning",
        "location": "HQ",
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=8)).isoformat(),
        "published": True,
    }
    payload.update(kw)
    return payload


def _employee_id(client, employee_token, auth_header):
    # Timeline of self returns the user's own id indirectly; instead decode via
    # a created request's user_id.
    r = client.post(
        "/requests", json={"type": "leave", "title": "x"}, headers=auth_header(employee_token)
    )
    return r.json()["user_id"]


def test_planner_creates_shift(client, planner_token, employee_token, auth_header):
    emp_id = _employee_id(client, employee_token, auth_header)
    r = client.post(
        "/planning/shifts", json=_shift_payload(emp_id), headers=auth_header(planner_token)
    )
    assert r.status_code == 201
    assert r.json()["published"] is True


def test_employee_cannot_create_shift(client, employee_token, auth_header):
    r = client.post(
        "/planning/shifts",
        json=_shift_payload("someone"),
        headers=auth_header(employee_token),
    )
    assert r.status_code == 403


def test_bulk_publish_and_delete(client, planner_token, employee_token, auth_header):
    emp_id = _employee_id(client, employee_token, auth_header)
    ids = []
    for _ in range(3):
        r = client.post(
            "/planning/shifts",
            json=_shift_payload(emp_id, published=False),
            headers=auth_header(planner_token),
        )
        ids.append(r.json()["id"])

    r = client.post(
        "/planning/shifts/bulk",
        json={"shift_ids": ids, "action": "publish"},
        headers=auth_header(planner_token),
    )
    assert r.status_code == 200
    assert r.json()["affected"] == 3

    r = client.post(
        "/planning/shifts/bulk",
        json={"shift_ids": ids[:2], "action": "delete"},
        headers=auth_header(planner_token),
    )
    assert r.json()["affected"] == 2
    # Deleted shifts no longer listed.
    listed = client.get("/planning/shifts", headers=auth_header(planner_token)).json()
    assert len(listed) == 1


def test_ics_feed_end_to_end(client, planner_token, employee_token, auth_header):
    emp_id = _employee_id(client, employee_token, auth_header)
    client.post(
        "/planning/shifts", json=_shift_payload(emp_id), headers=auth_header(planner_token)
    )
    # Employee provisions their personal feed token.
    r = client.post("/ics/token", headers=auth_header(employee_token))
    assert r.status_code == 201
    feed_url = r.json()["feed_url"]

    # Public feed renders valid ICS containing the published shift.
    r = client.get(feed_url)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")
    body = r.text
    assert "BEGIN:VCALENDAR" in body
    assert "BEGIN:VEVENT" in body
    assert "SUMMARY:Morning" in body


def test_ics_revoke_invalidates_feed(client, employee_token, auth_header):
    feed_url = client.post("/ics/token", headers=auth_header(employee_token)).json()["feed_url"]
    assert client.get(feed_url).status_code == 200
    assert client.post("/ics/token/revoke", headers=auth_header(employee_token)).status_code == 204
    assert client.get(feed_url).status_code == 404


def test_ics_unknown_token_404(client):
    assert client.get("/ics/feed/deadbeef.ics").status_code == 404
