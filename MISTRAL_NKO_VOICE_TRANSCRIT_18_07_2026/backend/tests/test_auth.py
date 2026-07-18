"""Auth: registration, login, refresh rotation + reuse detection, logout."""


def test_register_and_login(client, user_factory):
    email, tokens = user_factory()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"] != tokens["refresh_token"]


def test_duplicate_register(client, user_factory):
    email, _ = user_factory()
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "another-long-password"},
    )
    assert response.status_code == 409


def test_short_password_rejected(client):
    response = client.post(
        "/api/v1/auth/register", json={"email": "short@example.com", "password": "short"}
    )
    assert response.status_code == 422


def test_wrong_password(client, user_factory):
    email, _ = user_factory()
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password-here"}
    )
    assert response.status_code == 401


def test_unknown_user_same_response(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "whatever-password"},
    )
    assert response.status_code == 401


def test_refresh_rotation_and_reuse_detection(client, user_factory):
    _, tokens = user_factory()
    first_refresh = tokens["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200
    second_refresh = rotated.json()["refresh_token"]
    assert second_refresh != first_refresh

    # Reusing the rotated-out token must fail AND revoke the whole family.
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse.status_code == 401
    after_reuse = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second_refresh}
    )
    assert after_reuse.status_code == 401


def test_logout_revokes_refresh(client, user_factory):
    _, tokens = user_factory()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 401


def test_garbage_tokens_rejected(client):
    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"}
    ).status_code == 401
    assert client.get(
        "/api/v1/transcriptions", headers={"Authorization": "Bearer not-a-jwt"}
    ).status_code == 401


def test_access_token_not_valid_as_refresh(client, user_factory):
    _, tokens = user_factory()
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert response.status_code == 401
