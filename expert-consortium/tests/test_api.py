import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.rag.chat import ChatAnswer, rate_exchange

client = TestClient(app)
AUTH = {"X-Password": settings.web_password}


def test_health_needs_no_password():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_wrong_password_rejected():
    r = client.post("/api/login", headers={"X-Password": "nope"})
    assert r.status_code == 401


def test_right_password_accepted():
    assert client.post("/api/login", headers=AUTH).json() == {"ok": True}


def test_chat_endpoint_returns_answer_and_sources():
    fake = ChatAnswer(answer="Réponse [a.pdf]", sources=["a.pdf"], log_ts="2026-01-01T00:00:00")
    with patch("app.main.rag_chat.ask", return_value=fake) as mock_ask:
        r = client.post("/api/chat", headers=AUTH,
                        json={"question": "Q?", "domain": "law", "history": []})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].startswith("Réponse")
    assert body["sources"] == ["a.pdf"]
    mock_ask.assert_called_once_with("Q?", domain="law", history=[])


def test_chat_rejects_empty_question():
    r = client.post("/api/chat", headers=AUTH, json={"question": "", "domain": "all"})
    assert r.status_code == 422


def test_upload_rejects_unsupported_type():
    r = client.post("/api/upload", headers=AUTH,
                    files={"file": ("virus.exe", b"xx")}, data={"domain": "general"})
    assert r.status_code == 400


def test_upload_rejects_unknown_domain():
    r = client.post("/api/upload", headers=AUTH,
                    files={"file": ("a.txt", b"hello")}, data={"domain": "hacking"})
    assert r.status_code == 400


def test_rate_exchange_updates_log(tmp_path):
    with patch.object(settings, "logs_dir", tmp_path):
        log = tmp_path / "chat_log.jsonl"
        log.write_text(json.dumps({"ts": "T1", "question": "q", "rating": None}) + "\n")
        assert rate_exchange("T1", "good") is True
        assert json.loads(log.read_text())["rating"] == "good"
        assert rate_exchange("missing", "good") is False
