from app.config import get_settings
from tests.test_asr import make_wav


def test_consent_review_and_export(client, auth_headers, tmp_path):
    settings = get_settings()
    old_dir, old_key = settings.training_data_dir, settings.review_api_key
    settings.training_data_dir = str(tmp_path)
    settings.review_api_key = "review-test-key"
    try:
        response = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("sample.wav", make_wav(), "audio/wav")},
            data={"training_consent": "true", "language": "bam"},
        )
        assert response.status_code == 200
        review_headers = {"X-Review-Key": "review-test-key"}
        samples = client.get(
            "/api/training/samples", headers=review_headers
        ).json()
        sample = next(row for row in samples if row["transcription_id"] == response.json()["id"])
        reviewed = client.patch(
            f"/api/training/samples/{sample['id']}",
            headers=review_headers,
            json={
                "status": "approved",
                "corrected_text_latin": "i ni ce",
                "corrected_text_nko": "ߌ ߣߌ ߗߋ",
            },
        )
        assert reviewed.status_code == 200
        export = client.get("/api/training/export.csv", headers=review_headers)
        assert "i ni ce" in export.text
        assert client.get("/api/training/samples").status_code == 403
    finally:
        settings.training_data_dir = old_dir
        settings.review_api_key = old_key
