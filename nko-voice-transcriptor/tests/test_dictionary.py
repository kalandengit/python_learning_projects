"""Tests for the N'Ko ↔ French dictionary."""

from app.dictionary import Dictionary, Entry, get_dictionary


def _dict() -> Dictionary:
    return Dictionary(
        [
            Entry(fr="eau", nko="ߓߊߟߋ߲", cat="ߕ."),
            Entry(fr="maison", nko="ߓߏ߲", cat="ߕ."),
            Entry(fr="maisonnette", nko="ߓߏ߲ߘߋ߲", cat="ߕ."),
            Entry(fr="école", nko="ߞߊߙߊ߲ߘߊ", cat="ߕ."),
        ]
    )


class TestSearchFr:
    def test_exact_ranked_first(self):
        hits = _dict().search_fr("maison", 10)
        assert hits[0].fr == "maison"  # exact before "maisonnette" prefix

    def test_prefix(self):
        frs = [e.fr for e in _dict().search_fr("mais", 10)]
        assert "maison" in frs and "maisonnette" in frs

    def test_accent_insensitive(self):
        # "ecole" (no accent) must find "école"
        hits = _dict().search_fr("ecole", 10)
        assert hits and hits[0].fr == "école"

    def test_limit(self):
        assert len(_dict().search_fr("", 10)) == 0
        assert len(_dict().search_fr("m", 1)) == 1

    def test_no_match(self):
        assert _dict().search_fr("zzzznope", 10) == []


class TestSearchNko:
    def test_nko_lookup(self):
        hits = _dict().search_nko("ߓߏ߲", 10)
        assert hits[0].fr == "maison"

    def test_nko_substring(self):
        frs = [e.fr for e in _dict().search_nko("ߓߏ߲", 10)]
        assert "maisonnette" in frs  # ߓߏ߲ߘߋ߲ contains ߓߏ߲


class TestBundledLexicon:
    def test_full_lexicon_is_default(self):
        # With no NKO_LEXICON_PATH set, the bundled full French–N'Ko lexicon
        # loads (tens of thousands of entries), not just the small sample.
        d = get_dictionary()
        assert len(d) > 10_000
        assert d.search_fr("eau", 5)

    def test_common_words_present(self):
        d = get_dictionary()
        for word in ("maison", "eau", "paix", "bonjour"):
            assert d.search_fr(word, 1), f"{word!r} missing from lexicon"


class TestEndpoint:
    def test_lookup_fr(self, client):
        r = client.get("/api/dictionary", params={"q": "eau", "dir": "fr"})
        assert r.status_code == 200
        body = r.json()
        assert body["direction"] == "fr"
        assert body["count"] >= 1
        assert any(0x07C0 <= ord(c) <= 0x07FF for c in body["entries"][0]["nko"])

    def test_lookup_requires_query(self, client):
        assert client.get("/api/dictionary", params={"q": ""}).status_code == 422

    def test_bad_direction_rejected(self, client):
        assert client.get(
            "/api/dictionary", params={"q": "eau", "dir": "xx"}
        ).status_code == 422

    def test_public_no_auth(self, client):
        # dictionary is a public reference; no token needed
        assert client.get("/api/dictionary", params={"q": "eau"}).status_code == 200
