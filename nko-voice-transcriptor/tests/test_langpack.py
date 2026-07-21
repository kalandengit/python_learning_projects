"""Tests for the separate language-pack module (EN/RU/ZH/AR + full FR)."""

from app import langpack


class TestRegistry:
    def test_lists_all_languages(self):
        codes = {m.code for m in langpack.available_languages()}
        assert {"fr", "en", "ru", "zh", "ar"} <= codes

    def test_french_is_full_others_partial(self):
        by = {m.code: m for m in langpack.available_languages()}
        assert by["fr"].partial is False
        assert by["fr"].count > 10_000
        for code in ("en", "ru", "zh", "ar"):
            assert by[code].partial is True
            assert by[code].count > 0

    def test_french_first(self):
        assert langpack.available_languages()[0].code == "fr"

    def test_bambara_derived_full(self):
        by = {m.code: m for m in langpack.available_languages()}
        assert "bm" in by
        assert by["bm"].partial is False
        assert by["bm"].count > 10_000  # romanized from the whole lexicon


class TestBambara:
    def test_romanized_lookup(self):
        # "ji" is Bambara for water (N'Ko ߖߌ); romanized pack should find it
        hits = langpack.search("bm", "ji", "term", 5)
        assert hits and all(any(0x07C0 <= ord(c) <= 0x07FF for c in e.nko) for e in hits)

    def test_terms_are_latin(self):
        # romanized Bambara terms carry no N'Ko codepoints
        for e in langpack.get_pack("bm").entries[:200]:
            assert not any(0x07C0 <= ord(c) <= 0x07FF for c in e.fr)


class TestSearch:
    def test_each_language_maps_water_to_same_nko(self):
        pairs = {"en": "water", "ru": "вода", "zh": "水", "ar": "ماء", "fr": "eau"}
        nkos = set()
        for lang, term in pairs.items():
            hits = langpack.search(lang, term, "term", 1)
            assert hits, f"no hit for {lang} {term!r}"
            nkos.add(hits[0].nko)
        # all five languages resolve "water" to the same N'Ko headword
        assert nkos == {"ߓߊߟߋ߲"}

    def test_nko_reverse_lookup(self):
        hits = langpack.search("en", "ߓߊߟߋ߲", "nko", 5)
        assert any(e.fr == "water" for e in hits)

    def test_unknown_language_empty(self):
        assert langpack.search("xx", "water", "term", 5) == []

    def test_pack_nko_is_in_block(self):
        for e in langpack.get_pack("ar").entries:
            assert any(0x07C0 <= ord(c) <= 0x07FF for c in e.nko)


class TestEndpoints:
    def test_languages_endpoint(self, client):
        r = client.get("/api/langpack/languages")
        assert r.status_code == 200
        codes = {row["code"] for row in r.json()}
        assert {"fr", "en", "ru", "zh", "ar"} <= codes

    def test_lookup_en(self, client):
        r = client.get("/api/langpack/lookup", params={"q": "water", "lang": "en"})
        assert r.status_code == 200
        body = r.json()
        assert body["lang"] == "en" and body["count"] >= 1
        assert body["entries"][0]["nko"] == "ߓߊߟߋ߲"

    def test_lookup_arabic(self, client):
        r = client.get("/api/langpack/lookup", params={"q": "ماء", "lang": "ar"})
        assert r.status_code == 200 and r.json()["count"] >= 1

    def test_unknown_language_422(self, client):
        r = client.get("/api/langpack/lookup", params={"q": "x", "lang": "zz"})
        assert r.status_code == 422

    def test_bad_direction_422(self, client):
        r = client.get(
            "/api/langpack/lookup", params={"q": "water", "lang": "en", "dir": "xx"}
        )
        assert r.status_code == 422
