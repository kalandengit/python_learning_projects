def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_bootstrap_and_first_admin_flow(client, tenant):
    r = client.post(
        f"/auth/tenants/{tenant['id']}/first-admin",
        json={"email": "admin@acme.io", "full_name": "Ada"},
    )
    assert r.status_code == 201
    invite = r.json()["invite_token"]

    # Accept invite activates the account.
    r = client.post("/auth/accept-invite", json={"token": invite, "password": "adminpass123"})
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    # Login succeeds.
    r = client.post("/auth/login", json={"email": "admin@acme.io", "password": "adminpass123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_first_admin_blocked_when_users_exist(client, tenant, admin_token):
    r = client.post(
        f"/auth/tenants/{tenant['id']}/first-admin",
        json={"email": "another@acme.io"},
    )
    assert r.status_code == 409


def test_duplicate_slug_rejected(client, tenant):
    r = client.post("/auth/bootstrap-tenant", json={"name": "Acme 2", "slug": "acme"})
    assert r.status_code == 409


def test_invite_requires_admin(client, tenant, employee_token, auth_header):
    r = client.post(
        f"/auth/tenants/{tenant['id']}/invite",
        json={"email": "x@acme.io", "role": "employee"},
        headers=auth_header(employee_token),
    )
    assert r.status_code == 403


def test_wrong_password_rejected(client, tenant, admin_token):
    r = client.post("/auth/login", json={"email": "admin@acme.io", "password": "nope"})
    assert r.status_code == 401


def test_unknown_email_reset_returns_decoy(client, tenant):
    r = client.post("/auth/reset/request", json={"email": "ghost@acme.io"})
    assert r.status_code == 200
    assert r.json()["reset_token"]


def test_password_reset_flow(client, tenant, admin_token):
    r = client.post("/auth/reset/request", json={"email": "admin@acme.io"})
    token = r.json()["reset_token"]
    r = client.post("/auth/reset/confirm", json={"token": token, "password": "brandnew123"})
    assert r.status_code == 200
    # Old password no longer works; new one does.
    assert client.post(
        "/auth/login", json={"email": "admin@acme.io", "password": "adminpass123"}
    ).status_code == 401
    assert client.post(
        "/auth/login", json={"email": "admin@acme.io", "password": "brandnew123"}
    ).status_code == 200


def test_reset_token_single_use(client, tenant, admin_token):
    token = client.post("/auth/reset/request", json={"email": "admin@acme.io"}).json()[
        "reset_token"
    ]
    assert client.post(
        "/auth/reset/confirm", json={"token": token, "password": "firstchange1"}
    ).status_code == 200
    assert client.post(
        "/auth/reset/confirm", json={"token": token, "password": "secondchange1"}
    ).status_code == 400
