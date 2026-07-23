"""End-to-end smoke test using a generated WAV voice-like signal."""

from tests.test_asr import make_wav


def test_generated_voice_audio_transcribes_to_latin_and_nko(client, auth_headers):
    response = client.post(
        "/api/transcribe",
        headers=auth_headers,
        files={"audio": ("voice-smoke.wav", make_wav(), "audio/wav")},
        data={"language": "bam"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["language"] == "bam"
    assert result["text_latin"].strip()
    assert result["text_nko"].strip()
    assert any("\u07c0" <= char <= "\u07ff" for char in result["text_nko"])
