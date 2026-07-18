"""French↔N'Ko lexicon retrieval (exact > prefix > substring ranking)."""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

DEFAULT_LEXICON = Path(__file__).parent / "data" / "lexicon-fr-nko.json"
MAX_LIMIT = 50


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold().strip())
    return "".join(char for char in value if not unicodedata.combining(char))


class LexiconRetriever:
    def __init__(self, path: Path = DEFAULT_LEXICON):
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.entries = payload["entries"] if isinstance(payload, dict) else payload

    def search(self, query: str, direction: str = "fr", limit: int = 10) -> list[dict]:
        if direction not in {"fr", "nko"}:
            raise ValueError("direction must be 'fr' or 'nko'")
        limit = max(1, min(limit, MAX_LIMIT))
        needle = normalize(query) if direction == "fr" else query.strip()
        if not needle:
            return []
        matches = []
        for row in self.entries:
            value = normalize(row["fr"]) if direction == "fr" else row["nko"]
            if needle in value:
                rank = 0 if value == needle else 1 if value.startswith(needle) else 2
                matches.append((rank, len(value), value, row))
        return [item[3] for item in sorted(matches, key=lambda item: item[:3])[:limit]]


@lru_cache
def get_retriever() -> LexiconRetriever:
    return LexiconRetriever()
