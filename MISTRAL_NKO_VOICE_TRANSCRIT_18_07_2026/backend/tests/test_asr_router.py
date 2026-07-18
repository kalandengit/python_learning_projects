"""Engine routing: Manding → local, Voxtral languages → Mistral when configured."""

from pydantic import SecretStr

from app.asr.router import get_engine, route_language
from app.config import get_settings


def test_manding_routes_local():
    for code in ("bam", "dyu", "emk", "jul"):
        assert route_language(code) == "mock"  # test default engine


def test_french_without_key_falls_back_local():
    assert route_language("fr") == "mock"


def test_french_with_key_routes_voxtral(monkeypatch):
    monkeypatch.setattr(get_settings(), "mistral_api_key", SecretStr("k" * 32))
    assert route_language("fr") == "voxtral"
    # Bambara still local: Voxtral has no Manding support.
    assert route_language("bam") == "mock"


def test_override_wins():
    assert get_engine("bam", "voxtral").name == "voxtral"


def test_mock_transliteration_pipeline(wav_bytes):
    from app.nko import transliterate

    latin = get_engine("bam", "mock").transcribe(wav_bytes, "bam")
    assert latin.startswith("i ni ce")
    assert any("߀" <= ch <= "߿" for ch in transliterate(latin))
