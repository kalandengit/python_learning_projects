"""End-to-end API tests (mock ASR engine, in-memory SQLite)."""

import jwt

from app.config import get_settings
from tests.test_asr import make_wav


class TestHealth:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["asr_engine"] == "mock"

    def test_security_headers_present(self, client):
        r = client.get("/api/health")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" in r.headers
        assert r.headers["Permissions-Policy"] == "microphone=(self)"
        assert r.headers["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_sensitive_routes_disable_caching(self, client):
        r = client.post(
            "/api/auth/login",
            json={"username": "missing", "password": "not-a-real-password9"},
        )
        assert r.headers["Cache-Control"] == "no-store"

    def test_index_served(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "N'KO Voice Transcriptor" in r.text


class TestAuth:
    def test_registration_saves_profile_and_confirms_password(self, client):
        body = {
            "username": "profile-user", "password": "s3cure-passphrase!",
            "confirm_password": "s3cure-passphrase!", "first_name": "Aminata",
            "last_name": "Kante", "email": "aminata@example.org",
        }
        response = client.post("/api/auth/register", json=body)
        assert response.status_code == 201
        assert response.json()["first_name"] == "Aminata"
        assert response.json()["email"] == "aminata@example.org"

    def test_registration_rejects_password_mismatch(self, client):
        response = client.post("/api/auth/register", json={
            "username": "mismatch", "password": "s3cure-passphrase!",
            "confirm_password": "different-passphrase2!",
        })
        assert response.status_code == 422

    def test_social_providers_are_hidden_without_credentials(self, client):
        response = client.get("/api/auth/oauth/providers")
        assert response.status_code == 200
        assert response.json() == {"google": False, "facebook": False}

    def test_register_login_flow(self, client):
        creds = {"username": "alice", "password": "s3cure-passphrase!"}
        r = client.post("/api/auth/register", json=creds)
        assert r.status_code == 201
        assert "password" not in r.text  # never echo password material

        r = client.post("/api/auth/login", json=creds)
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_duplicate_username_conflict(self, client):
        creds = {"username": "bob", "password": "s3cure-passphrase!"}
        assert client.post("/api/auth/register", json=creds).status_code == 201
        assert client.post("/api/auth/register", json=creds).status_code == 409

    def test_wrong_password_401(self, client):
        creds = {"username": "carol", "password": "s3cure-passphrase!"}
        client.post("/api/auth/register", json=creds)
        r = client.post(
            "/api/auth/login",
            json={"username": "carol", "password": "wrong-password-99"},
        )
        assert r.status_code == 401

    def test_unknown_user_same_error_as_bad_password(self, client):
        r = client.post(
            "/api/auth/login",
            json={"username": "nobody-here", "password": "wrong-password-99"},
        )
        assert r.status_code == 401  # no username enumeration
        assert r.json()["detail"] == "Invalid credentials"

    def test_unknown_user_login_spends_argon2_work(self, client, monkeypatch):
        # The unknown-user path must run a dummy Argon2 verify so its timing
        # matches a real wrong-password check (no enumeration by response time).
        import app.routes.auth as auth_mod

        called = {"dummy": False}
        real = auth_mod.verify_dummy
        monkeypatch.setattr(
            auth_mod, "verify_dummy",
            lambda pw: (called.__setitem__("dummy", True), real(pw))[1],
        )
        r = client.post(
            "/api/auth/login",
            json={"username": "ghost-user-xyz", "password": "wrong-password-99"},
        )
        assert r.status_code == 401
        assert called["dummy"] is True

    def test_weak_password_rejected(self, client):
        r = client.post(
            "/api/auth/register",
            json={"username": "dave", "password": "short"},
        )
        assert r.status_code == 422
        r = client.post(
            "/api/auth/register",
            json={"username": "dave", "password": "onlyletterspassword"},
        )
        assert r.status_code == 422

    def test_bad_username_pattern_rejected(self, client):
        r = client.post(
            "/api/auth/register",
            json={"username": "evil user!<script>", "password": "s3cure-pass!"},
        )
        assert r.status_code == 422


class TestTranscribe:
    def test_requires_auth(self, client):
        r = client.post(
            "/api/transcribe",
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 401

    def test_transcribe_wav(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["engine"] == "mock"
        assert body["text_latin"]
        # N'Ko output must be in the N'Ko Unicode block
        nko_chars = [c for c in body["text_nko"] if not c.isspace()]
        assert nko_chars
        assert all(0x061F == ord(c) or 0x07C0 <= ord(c) <= 0x07FF for c in nko_chars)

    def test_garbage_upload_rejected(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("x.wav", b"MZ\x90\x00 not audio", "audio/wav")},
        )
        assert r.status_code == 422

    def test_wrong_mime_rejected(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("x.exe", make_wav(), "application/octet-stream")},
        )
        assert r.status_code == 422

    def test_too_long_wav_rejected(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("long.wav", make_wav(seconds=200), "audio/wav")},
        )
        assert r.status_code == 422

    def test_invalid_token_401(self, client):
        r = client.post(
            "/api/transcribe",
            headers={"Authorization": "Bearer not.a.jwt"},
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 401

    def test_non_numeric_token_subject_401(self, client):
        settings = get_settings()
        token = jwt.encode(
            {"sub": "not-a-user-id", "type": "access", "exp": 4_102_444_800},
            settings.secret_key,
            algorithm="HS256",
        )
        r = client.post(
            "/api/transcribe",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 401


class TestTransliterateEndpoint:
    def test_text_conversion(self, client):
        r = client.post("/api/transliterate", json={"text": "i ni ce"})
        assert r.status_code == 200
        assert r.json()["text_nko"] == "ߌ ߣߌ ߗߋ"

    def test_empty_rejected(self, client):
        assert client.post("/api/transliterate", json={"text": ""}).status_code == 422

    def test_oversize_rejected(self, client):
        r = client.post("/api/transliterate", json={"text": "a" * 30_000})
        assert r.status_code == 422


class TestHistory:
    def test_history_lists_own_transcriptions(self, client, auth_headers):
        before = client.get("/api/history", headers=auth_headers).json()
        client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(seconds=0.5), "audio/wav")},
        )
        after = client.get("/api/history", headers=auth_headers).json()
        assert len(after) == len(before) + 1
        assert after[0]["text_nko"]

    def test_history_requires_auth(self, client):
        assert client.get("/api/history").status_code == 401

    def test_cannot_touch_other_users_rows(self, client, auth_headers):
        # user A creates a row
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        row_id = r.json()["id"]
        # user B registers and tries to read/edit/delete it
        creds = {"username": "mallory", "password": "s3cure-passphrase!"}
        client.post("/api/auth/register", json=creds)
        tok = client.post("/api/auth/login", json=creds).json()["access_token"]
        b_headers = {"Authorization": f"Bearer {tok}"}
        assert all(t["id"] != row_id for t in client.get("/api/history", headers=b_headers).json())
        assert client.patch(
            f"/api/history/{row_id}", headers=b_headers, json={"text_nko": "ߤߊߞߍ"}
        ).status_code == 404
        assert client.delete(f"/api/history/{row_id}", headers=b_headers).status_code == 404
        # owner can delete
        assert client.delete(f"/api/history/{row_id}", headers=auth_headers).status_code == 204


class TestEditTranscription:
    def _create(self, client, headers):
        return client.post(
            "/api/transcribe",
            headers=headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        ).json()["id"]

    def test_edit_saves_corrected_nko(self, client, auth_headers):
        row_id = self._create(client, auth_headers)
        corrected = "ߒ ߓߍ ߕߊ߭"
        r = client.patch(
            f"/api/history/{row_id}", headers=auth_headers, json={"text_nko": corrected}
        )
        assert r.status_code == 200
        assert r.json()["text_nko"] == corrected
        # persisted
        rows = client.get("/api/history", headers=auth_headers).json()
        assert next(t for t in rows if t["id"] == row_id)["text_nko"] == corrected

    def test_edit_requires_auth(self, client, auth_headers):
        row_id = self._create(client, auth_headers)
        assert client.patch(f"/api/history/{row_id}", json={"text_nko": "x"}).status_code == 401

    def test_edit_missing_row_404(self, client, auth_headers):
        assert client.patch(
            "/api/history/999999", headers=auth_headers, json={"text_nko": "x"}
        ).status_code == 404

    def test_edit_allows_empty_string(self, client, auth_headers):
        row_id = self._create(client, auth_headers)
        r = client.patch(
            f"/api/history/{row_id}", headers=auth_headers, json={"text_nko": ""}
        )
        assert r.status_code == 200
        assert r.json()["text_nko"] == ""

    def test_edit_rejects_oversize(self, client, auth_headers):
        row_id = self._create(client, auth_headers)
        r = client.patch(
            f"/api/history/{row_id}", headers=auth_headers, json={"text_nko": "ߊ" * 20_001}
        )
        assert r.status_code == 422
