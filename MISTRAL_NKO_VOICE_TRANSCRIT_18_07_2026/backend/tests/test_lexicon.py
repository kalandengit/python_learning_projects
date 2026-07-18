"""Lexicon retrieval: ranking, directions, limits, API endpoint."""

import pytest

from app.retrieval import get_retriever


def test_exact_match_first():
    results = get_retriever().search("maison")
    assert results and results[0]["fr"].casefold() == "maison"


def test_accent_insensitive():
    with_accent = get_retriever().search("éléphant")
    without = get_retriever().search("elephant")
    assert with_accent == without


def test_nko_direction():
    nko_word = get_retriever().search("maison")[0]["nko"]
    back = get_retriever().search(nko_word, direction="nko")
    assert any(row["nko"] == nko_word for row in back)


def test_bad_direction():
    with pytest.raises(ValueError):
        get_retriever().search("a", direction="xx")


def test_limit_clamped():
    assert len(get_retriever().search("a", limit=10_000)) <= 50


def test_api_endpoint(client):
    response = client.get("/api/v1/lexicon/search", params={"q": "maison"})
    assert response.status_code == 200
    assert response.json()["results"][0]["fr"].casefold() == "maison"


def test_api_rejects_bad_direction(client):
    response = client.get(
        "/api/v1/lexicon/search", params={"q": "a", "direction": "zz"}
    )
    assert response.status_code == 422


def test_catalogs(client):
    languages = client.get("/api/v1/languages").json()["languages"]
    assert any(lang["code"] == "bam" for lang in languages)
    engines = client.get("/api/v1/asr/engines").json()["engines"]
    assert {e["id"] for e in engines} >= {"mock", "mms", "whisper", "voxtral"}
