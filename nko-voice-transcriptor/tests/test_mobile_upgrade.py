from tests.test_asr import make_wav


def fresh_user(client, username):
    credentials = {"username": username, "password": "s3cure-passphrase!"}
    assert client.post("/api/auth/register", json=credentials).status_code == 201
    login = client.post("/api/auth/login", json=credentials)
    return credentials, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_refresh_cookie_rotates_access_token(client):
    credentials, _ = fresh_user(client, "refresh-user")
    refreshed = client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert client.post("/api/auth/logout").status_code == 204
    assert client.post("/api/auth/refresh").status_code == 401
    assert credentials["username"] == "refresh-user"


def test_background_job_segments_and_subtitles(client):
    _, headers = fresh_user(client, "mobile-job-user")
    created = client.post(
        "/api/jobs/transcribe",
        headers=headers,
        files={"audio": ("voice.wav", make_wav(seconds=1), "audio/wav")},
        data={"language": "bam"},
    )
    assert created.status_code == 202
    job = client.get(f"/api/jobs/{created.json()['id']}", headers=headers).json()
    assert job["status"] == "completed"
    result = client.get(
        f"/api/jobs/{created.json()['id']}/result", headers=headers
    ).json()
    segments = client.get(
        f"/api/history/{result['id']}/segments", headers=headers
    ).json()
    assert segments and segments[0]["start_ms"] == 0
    vtt = client.get(
        f"/api/history/{result['id']}/subtitles?format=vtt&script=nko",
        headers=headers,
    )
    assert vtt.status_code == 200
    assert vtt.text.startswith("WEBVTT")


def test_history_export_and_account_deletion(client):
    credentials, headers = fresh_user(client, "delete-mobile-user")
    export = client.get("/api/history/export.csv", headers=headers)
    assert export.status_code == 200 and export.text.startswith("id,created_at")
    deleted = client.request(
        "DELETE",
        "/api/auth/account",
        headers=headers,
        json={"password": credentials["password"]},
    )
    assert deleted.status_code == 204
    assert client.post("/api/auth/login", json=credentials).status_code == 401
