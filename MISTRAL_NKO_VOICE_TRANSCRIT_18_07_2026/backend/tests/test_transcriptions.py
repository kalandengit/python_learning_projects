"""Upload validation, transcription pipeline, history, IDOR protection."""

from tests.conftest import make_wav


def _upload(client, data, headers=None, **form):
    files = {"audio": ("test.wav", data, form.pop("mime", "audio/wav"))}
    payload = {"language": "bam", **form}
    return client.post(
        "/api/v1/transcriptions/upload", files=files, data=payload, headers=headers or {}
    )


def test_anonymous_transcription(client, wav_bytes):
    response = _upload(client, wav_bytes)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["asr_engine"] == "mock"
    assert body["latin_text"].startswith("i ni ce")
    assert any("߀" <= ch <= "߿" for ch in body["nko_text"])
    assert body["id"] is None  # nothing stored without auth + opt-in


def test_bad_mime_rejected(client, wav_bytes):
    assert _upload(client, wav_bytes, mime="text/plain").status_code == 415


def test_bad_magic_bytes_rejected(client):
    assert _upload(client, b"definitely not audio bytes").status_code == 415


def test_bad_language_rejected(client, wav_bytes):
    assert _upload(client, wav_bytes, language="xx").status_code == 422


def test_unknown_engine_rejected(client, wav_bytes):
    assert _upload(client, wav_bytes, asr_engine="skynet").status_code == 422


def test_oversize_rejected_via_endpoint(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_bytes", 200)
    big = make_wav(b"\x00" * 5_000)
    assert _upload(client, big).status_code == 413


def test_history_opt_in_and_idor(client, wav_bytes, user_factory):
    _, tokens_a = user_factory()
    _, tokens_b = user_factory()
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    stored = _upload(client, wav_bytes, headers=headers_a, store_history="true")
    assert stored.status_code == 200
    transcript_id = stored.json()["id"]
    assert transcript_id is not None

    # Owner sees it.
    own = client.get(f"/api/v1/transcriptions/{transcript_id}", headers=headers_a)
    assert own.status_code == 200
    listing = client.get("/api/v1/transcriptions", headers=headers_a)
    assert any(row["id"] == transcript_id for row in listing.json())

    # Cross-user access is 404, indistinguishable from not-found (IDOR).
    cross = client.get(f"/api/v1/transcriptions/{transcript_id}", headers=headers_b)
    assert cross.status_code == 404
    cross_delete = client.delete(
        f"/api/v1/transcriptions/{transcript_id}", headers=headers_b
    )
    assert cross_delete.status_code == 404

    # Owner can delete.
    assert (
        client.delete(f"/api/v1/transcriptions/{transcript_id}", headers=headers_a)
        .status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/transcriptions/{transcript_id}", headers=headers_a)
        .status_code
        == 404
    )


def test_history_requires_auth(client):
    assert client.get("/api/v1/transcriptions").status_code == 401
