from tests.conftest import make_user


def _make_request(client, token, auth_header):
    return client.post(
        "/requests", json={"type": "absence", "title": "Sick"}, headers=auth_header(token)
    ).json()


def test_upload_clean_file_is_available(client, employee_token, auth_header):
    req = _make_request(client, employee_token, auth_header)
    r = client.post(
        f"/requests/{req['id']}/attachments",
        files={"file": ("note.pdf", b"%PDF-1.4 clean content", "application/pdf")},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["scan_status"] == "clean"
    assert body["is_available"] is True


def test_upload_rejects_disallowed_type(client, employee_token, auth_header):
    req = _make_request(client, employee_token, auth_header)
    r = client.post(
        f"/requests/{req['id']}/attachments",
        files={"file": ("x.exe", b"MZ", "application/octet-stream")},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 415


def test_infected_file_not_available_and_not_downloadable(
    client, employee_token, auth_header
):
    req = _make_request(client, employee_token, auth_header)
    r = client.post(
        f"/requests/{req['id']}/attachments",
        files={"file": ("bad.png", b"STAFFHUB-EICAR-TEST payload", "image/png")},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 201
    att = r.json()
    assert att["scan_status"] == "infected"
    assert att["is_available"] is False

    r = client.get(
        f"/requests/{req['id']}/attachments/{att['id']}/download",
        headers=auth_header(employee_token),
    )
    assert r.status_code == 409


def test_medical_document_is_hr_only(client, tenant, admin_token, employee_token, auth_header):
    req = _make_request(client, employee_token, auth_header)
    att = client.post(
        f"/requests/{req['id']}/attachments",
        data={"is_medical": "true"},
        files={"file": ("med.pdf", b"%PDF medical", "application/pdf")},
        headers=auth_header(employee_token),
    ).json()

    # A planner (not HR) cannot see or download the medical document.
    planner = make_user(client, tenant["id"], admin_token, "pl@acme.io", "planner")
    listed = client.get(
        f"/requests/{req['id']}/attachments", headers=auth_header(planner)
    ).json()
    assert att["id"] not in [a["id"] for a in listed]
    r = client.get(
        f"/requests/{req['id']}/attachments/{att['id']}/download",
        headers=auth_header(planner),
    )
    assert r.status_code == 403

    # HR can download it.
    hr = make_user(client, tenant["id"], admin_token, "hr@acme.io", "hr")
    r = client.get(
        f"/requests/{req['id']}/attachments/{att['id']}/download",
        headers=auth_header(hr),
    )
    assert r.status_code == 200


def test_download_clean_owner(client, employee_token, auth_header):
    req = _make_request(client, employee_token, auth_header)
    att = client.post(
        f"/requests/{req['id']}/attachments",
        files={"file": ("ok.jpg", b"\xff\xd8\xff clean jpeg", "image/jpeg")},
        headers=auth_header(employee_token),
    ).json()
    r = client.get(
        f"/requests/{req['id']}/attachments/{att['id']}/download",
        headers=auth_header(employee_token),
    )
    assert r.status_code == 200
    assert r.json()["filename"] == "ok.jpg"
