"""Security regression tests: headers, body limit, health, rate limiting."""

from pydantic import SecretStr

from app.config import get_settings
from app.limits import limiter


def test_security_headers_present(client):
    response = client.get("/api/health")
    headers = response.headers
    assert "unsafe-inline" not in headers["content-security-policy"]
    assert "default-src 'self'" in headers["content-security-policy"]
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "microphone=(self)" in headers["permissions-policy"]


def test_health_is_minimal(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_detailed_health_locked_down(client, monkeypatch):
    # No token configured → always 403.
    assert client.get("/api/health/detailed").status_code == 403
    monkeypatch.setattr(
        get_settings(), "internal_health_token", SecretStr("internal-health-secret")
    )
    assert client.get("/api/health/detailed").status_code == 403
    ok = client.get(
        "/api/health/detailed", headers={"X-Internal-Health": "internal-health-secret"}
    )
    assert ok.status_code == 200
    assert "version" in ok.json()


def test_body_limit_rejects_declared_oversize(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 100)
    response = client.post(
        "/api/v1/transcriptions/upload",
        content=b"x" * 1_000,
        headers={"Content-Type": "multipart/form-data; boundary=x"},
    )
    assert response.status_code == 413


def test_login_rate_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_auth", "3/minute")
    limiter.reset()
    payload = {"email": "ratelimit@example.com", "password": "wrong-password-abc"}
    statuses = [
        client.post("/api/v1/auth/login", json=payload).status_code for _ in range(4)
    ]
    limiter.reset()
    assert statuses[:3] == [401, 401, 401]
    assert statuses[3] == 429


def test_secret_key_length_enforced():
    import pytest
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(secret_key="too-short", _env_file=None)
