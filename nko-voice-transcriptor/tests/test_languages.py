"""Tests for source-language selection."""

from app.asr.mock import MockASREngine
from tests.test_asr import make_settings, make_wav


class TestLanguagesEndpoint:
    def test_lists_defaults_first(self, client):
        langs = client.get("/api/languages").json()
        assert langs[0]["code"] == "bam"
        assert langs[0]["default"] is True
        codes = {lang["code"] for lang in langs}
        assert {"bam", "dyu", "emk", "mku", "msc", "mwk"} <= codes
        assert all(lang["name"] for lang in langs)


class TestTranscribeLanguage:
    def test_language_recorded(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
            data={"language": "dyu"},
        )
        assert r.status_code == 200
        assert r.json()["language"] == "dyu"

    def test_default_language_when_omitted(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 200
        assert r.json()["language"] == "bam"

    def test_unsupported_language_rejected(self, client, auth_headers):
        r = client.post(
            "/api/transcribe",
            headers=auth_headers,
            files={"audio": ("a.wav", make_wav(), "audio/wav")},
            data={"language": "fra"},
        )
        assert r.status_code == 422
        assert "Unsupported language" in r.json()["detail"]


class TestMockEngineLanguages:
    def test_language_flows_through(self):
        result = MockASREngine().transcribe(make_wav(), "wav", language="emk")
        assert result.language == "emk"
        assert result.text_latin

    def test_unknown_language_falls_back(self):
        # engine-level fallback; the API validates before reaching here
        result = MockASREngine().transcribe(make_wav(), "wav", language="mwk")
        assert result.language == "mwk"
        assert result.text_latin


class TestConfig:
    def test_default_language_must_be_offered(self):
        import pytest

        with pytest.raises(ValueError, match="NKO_DEFAULT_LANGUAGE"):
            make_settings(languages="bam,dyu", default_language="emk")

    def test_language_list_parsing(self):
        settings = make_settings(languages=" bam , dyu ")
        assert settings.language_list == ["bam", "dyu"]
