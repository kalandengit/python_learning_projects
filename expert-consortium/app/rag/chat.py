"""Chat orchestration: retrieve -> prompt -> Mistral -> log the exchange."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.config import settings, setup_logging
from app.mistral_client import get_client, with_retry
from app.rag.persona import build_messages
from app.rag.retriever import retrieve

logger = setup_logging()

MAX_HISTORY_MESSAGES = 12  # keep the last N turns to bound cost


@dataclass
class ChatAnswer:
    answer: str
    sources: list[str] = field(default_factory=list)
    log_ts: str = ""  # identifies the log line, used by the rating endpoint


def ask(
    question: str,
    domain: str | None = None,
    history: list[dict] | None = None,
) -> ChatAnswer:
    """Answer one question with RAG. ``history`` is prior [{role, content}] turns."""
    chunks = retrieve(question, domain=domain)
    context_blocks = [(c.source_file, c.text) for c in chunks]
    trimmed_history = (history or [])[-MAX_HISTORY_MESSAGES:]

    messages = build_messages(question, context_blocks, trimmed_history)
    resp = with_retry(
        get_client().chat.complete,
        model=settings.chat_model,
        messages=messages,
        temperature=0.3,
    )
    answer = resp.choices[0].message.content or ""

    sources = sorted({c.source_file for c in chunks})
    ts = _log_exchange(question, answer, sources, domain)
    return ChatAnswer(answer=answer, sources=sources, log_ts=ts)


def _log_exchange(
    question: str, answer: str, sources: list[str], domain: str | None
) -> str:
    """Append to the JSONL chat log — the raw material for fine-tuning (Milestone 5)."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "sources": sources,
        "domain": domain or "all",
        "model": settings.chat_model,
        "rating": None,  # set to "good" via the UI thumbs-up to include in fine-tuning
    }
    path = settings.logs_dir / "chat_log.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record["ts"]


def rate_exchange(log_ts: str, rating: str) -> bool:
    """Set the rating ('good'/'bad') on a logged exchange. Returns True if found."""
    path = settings.logs_dir / "chat_log.jsonl"
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("ts") == log_ts:
            record["rating"] = rating
            lines[i] = json.dumps(record, ensure_ascii=False)
            found = True
            break
    if found:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return found
