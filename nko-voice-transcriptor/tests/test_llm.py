"""Optional LLM cleanup tests; no external calls are made."""

import io
import json

from app.llm import improve_transcript
from tests.test_asr import make_settings


def test_disabled_returns_original():
    assert improve_transcript("ani sogoma", "bam", make_settings()) == "ani sogoma"


def test_openai_compatible_response(monkeypatch):
    settings = make_settings(llm_provider="groq", llm_api_key="secret")
    body = {"choices": [{"message": {"content": "ani sɔgɔma"}}]}
    response = io.BytesIO(json.dumps(body).encode())
    response.__enter__ = lambda self: self
    response.__exit__ = lambda *args: None
    monkeypatch.setattr("app.llm.urlopen", lambda request, timeout: response)
    assert improve_transcript("ani sogoma", "bam", settings) == "ani sɔgɔma"


def test_provider_failure_keeps_asr_text(monkeypatch):
    settings = make_settings(llm_provider="openai", llm_api_key="secret")
    def timeout(request, timeout):
        raise TimeoutError

    monkeypatch.setattr("app.llm.urlopen", timeout)
    assert improve_transcript("original", "bam", settings) == "original"
