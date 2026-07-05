import pytest

from app.models import ALLOWED_TRANSITIONS, RequestState
from app.services.requests import can_transition


def _create_draft(client, token, auth_header, type_="leave"):
    r = client.post(
        "/requests",
        json={"type": type_, "title": "Holiday", "body": "Two weeks"},
        headers=auth_header(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_state_machine_allowed_transitions_table():
    # Terminal states are dead ends.
    for terminal in (RequestState.APPROVED, RequestState.REJECTED, RequestState.CANCELLED):
        assert ALLOWED_TRANSITIONS[terminal] == set()
    assert can_transition(RequestState.DRAFT, RequestState.SUBMITTED)
    assert not can_transition(RequestState.DRAFT, RequestState.APPROVED)
    assert can_transition(RequestState.NEEDS_INFORMATION, RequestState.RESUBMITTED)


def test_create_and_edit_draft(client, employee_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    assert req["state"] == "draft"
    r = client.patch(
        f"/requests/{req['id']}",
        json={"title": "Updated"},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


def test_full_happy_path_to_approved(client, employee_token, planner_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    rid = req["id"]

    def transition(token, target, note=None):
        return client.post(
            f"/requests/{rid}/transition",
            json={"target": target, "note": note},
            headers=auth_header(token),
        )

    assert transition(employee_token, "submitted").status_code == 200
    assert transition(planner_token, "under_review").status_code == 200
    assert transition(planner_token, "needs_information", "Provide dates").status_code == 200
    assert transition(employee_token, "resubmitted").status_code == 200
    r = transition(planner_token, "approved", "Looks good")
    assert r.status_code == 200
    detail = r.json()
    assert detail["state"] == "approved"
    # History captured each transition.
    assert [h["to_state"] for h in detail["history"]] == [
        "submitted", "under_review", "needs_information", "resubmitted", "approved",
    ]


def test_illegal_transition_rejected(client, employee_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    r = client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "approved"},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 409


def test_employee_cannot_approve(client, employee_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "submitted"},
        headers=auth_header(employee_token),
    )
    # Employee attempting a planner-only transition is forbidden.
    r = client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "under_review"},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 403


def test_cannot_edit_non_draft(client, employee_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    client.post(
        f"/requests/{req['id']}/transition",
        json={"target": "submitted"},
        headers=auth_header(employee_token),
    )
    r = client.patch(
        f"/requests/{req['id']}",
        json={"title": "too late"},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 409


def test_transition_notifies_requester(client, employee_token, planner_token, auth_header):
    req = _create_draft(client, employee_token, auth_header)
    rid = req["id"]
    client.post(
        f"/requests/{rid}/transition",
        json={"target": "submitted"},
        headers=auth_header(employee_token),
    )
    client.post(
        f"/requests/{rid}/transition",
        json={"target": "under_review"},
        headers=auth_header(planner_token),
    )
    # Employee has an unread notification about the planner's action.
    r = client.get("/notifications?unread_only=true", headers=auth_header(employee_token))
    assert r.status_code == 200
    assert any("/requests/" in (n["deep_link"] or "") for n in r.json())
