from tests.conftest import make_user


def _second_tenant_admin(client):
    t = client.post("/auth/bootstrap-tenant", json={"name": "Beta", "slug": "beta"}).json()
    r = client.post(
        f"/auth/tenants/{t['id']}/first-admin", json={"email": "b-admin@beta.io"}
    )
    invite = r.json()["invite_token"]
    client.post("/auth/accept-invite", json={"token": invite, "password": "betapass123"})
    token = client.post(
        "/auth/login", json={"email": "b-admin@beta.io", "password": "betapass123"}
    ).json()["access_token"]
    return t, token


def test_tenant_isolation_on_requests(client, tenant, employee_token, auth_header):
    # Employee in tenant A creates a request.
    req = client.post(
        "/requests", json={"type": "leave", "title": "A-only"}, headers=auth_header(employee_token)
    ).json()

    # Admin of tenant B cannot read tenant A's request.
    _, b_token = _second_tenant_admin(client)
    r = client.get(f"/requests/{req['id']}", headers=auth_header(b_token))
    assert r.status_code == 404


def test_cross_tenant_invite_denied(client, tenant, admin_token, auth_header):
    other_tenant, _ = _second_tenant_admin(client)
    r = client.post(
        f"/auth/tenants/{other_tenant['id']}/invite",
        json={"email": "x@beta.io", "role": "employee"},
        headers=auth_header(admin_token),
    )
    assert r.status_code == 403


def test_feature_flags_upsert_and_isolation(client, tenant, admin_token, auth_header):
    r = client.put(
        "/admin/feature-flags",
        json={"key": "background_sync", "enabled": True},
        headers=auth_header(admin_token),
    )
    assert r.status_code == 200
    assert r.json() == {"key": "background_sync", "enabled": True}

    # Toggle off (upsert path).
    r = client.put(
        "/admin/feature-flags",
        json={"key": "background_sync", "enabled": False},
        headers=auth_header(admin_token),
    )
    assert r.json()["enabled"] is False

    flags = client.get("/admin/feature-flags", headers=auth_header(admin_token)).json()
    assert len(flags) == 1

    # A different tenant sees none of tenant A's flags.
    _, b_token = _second_tenant_admin(client)
    assert client.get("/admin/feature-flags", headers=auth_header(b_token)).json() == []


def test_feature_flags_require_admin(client, employee_token, auth_header):
    r = client.get("/admin/feature-flags", headers=auth_header(employee_token))
    assert r.status_code == 403


def test_login_rate_limit(client, tenant, admin_token):
    # admin_token fixture already performed one login. Hammer login to trip the
    # limiter (default 10 per window).
    codes = [
        client.post(
            "/auth/login", json={"email": "admin@acme.io", "password": "wrong"}
        ).status_code
        for _ in range(15)
    ]
    assert 429 in codes
