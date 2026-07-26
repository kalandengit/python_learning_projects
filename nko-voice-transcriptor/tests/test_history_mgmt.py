"""Tests for history management: search, count, clear-all."""

from tests.test_asr import make_wav


def _fresh_user(client, name):
    creds = {"username": name, "password": "s3cure-passphrase!"}
    client.post("/api/auth/register", json=creds)
    tok = client.post("/api/auth/login", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make(client, headers, n=1):
    ids = []
    for i in range(n):
        r = client.post(
            "/api/transcribe",
            headers=headers,
            files={"audio": ("a.wav", make_wav(seconds=0.3 + i * 0.05), "audio/wav")},
        )
        ids.append(r.json()["id"])
    return ids


class TestCount:
    def test_count_reflects_rows(self, client):
        h = _fresh_user(client, "counter")
        assert client.get("/api/history/count", headers=h).json()["count"] == 0
        _make(client, h, 3)
        assert client.get("/api/history/count", headers=h).json()["count"] == 3

    def test_count_requires_auth(self, client):
        assert client.get("/api/history/count").status_code == 401


class TestSearch:
    def test_search_filters(self, client):
        h = _fresh_user(client, "searcher")
        rid = _make(client, h, 1)[0]
        # tag a known needle onto the row via edit
        client.patch(f"/api/history/{rid}", headers=h, json={"text_nko": "ߞߊߺNEEDLEߺߊ"})
        hit = client.get("/api/history", headers=h, params={"q": "NEEDLE"}).json()
        assert len(hit) == 1 and hit[0]["id"] == rid
        miss = client.get("/api/history", headers=h, params={"q": "zzzznope"}).json()
        assert miss == []

    def test_search_matches_latin(self, client):
        h = _fresh_user(client, "searcher2")
        _make(client, h, 1)
        # mock latin phrases are known; "ni" appears in several
        rows = client.get("/api/history", headers=h, params={"q": "ni"}).json()
        assert all("ni" in r["text_latin"] for r in rows)


class TestClearAll:
    def test_clear_deletes_only_own(self, client):
        a = _fresh_user(client, "clear_a")
        b = _fresh_user(client, "clear_b")
        _make(client, a, 3)
        b_ids = _make(client, b, 2)
        resp = client.request("DELETE", "/api/history", headers=a)
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 3
        # A is empty, B untouched
        assert client.get("/api/history/count", headers=a).json()["count"] == 0
        assert client.get("/api/history/count", headers=b).json()["count"] == 2
        assert {r["id"] for r in client.get("/api/history", headers=b).json()} == set(b_ids)

    def test_clear_requires_auth(self, client):
        assert client.request("DELETE", "/api/history").status_code == 401


class TestPagination:
    def test_offset_limit(self, client):
        h = _fresh_user(client, "pager")
        _make(client, h, 5)
        page1 = client.get("/api/history", headers=h, params={"limit": 2, "offset": 0}).json()
        page2 = client.get("/api/history", headers=h, params={"limit": 2, "offset": 2}).json()
        assert len(page1) == 2 and len(page2) == 2
        assert {r["id"] for r in page1}.isdisjoint({r["id"] for r in page2})
