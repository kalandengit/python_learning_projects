"""N'Ko ↔ French dictionary lookup.

Data originates from the NKo Wuruki / N'Ko Institute lexicon
(https://www.nkowuruki.net/lexique-nkofr.html). The repository bundles only a
small **attributed sample** (``app/data/lexicon-sample.json``); a deployment
can point ``NKO_LEXICON_PATH`` at the full dataset it is licensed to use.

Lookup is in-memory and case/accent-insensitive on the French side. Matches
are ranked exact → prefix → substring so the most relevant entries surface
first. This is a read-only feature: no user data is involved.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

_SAMPLE_PATH = Path(__file__).parent / "data" / "lexicon-sample.json"


@dataclass(frozen=True)
class Entry:
    fr: str
    nko: str
    cat: str = ""


def _fold(text: str) -> str:
    """Lowercase and strip accents for accent-insensitive French matching."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


class Dictionary:
    def __init__(self, entries: list[Entry]) -> None:
        self.entries = entries
        self._fr_fold = [(_fold(e.fr), e) for e in entries]

    def __len__(self) -> int:
        return len(self.entries)

    @staticmethod
    def _rank(hay: str, needle: str) -> int | None:
        """0 exact, 1 prefix, 2 substring, None no match."""
        if hay == needle:
            return 0
        if hay.startswith(needle):
            return 1
        if needle in hay:
            return 2
        return None

    def search_fr(self, query: str, limit: int) -> list[Entry]:
        q = _fold(query.strip())
        if not q:
            return []
        scored: list[tuple[int, int, Entry]] = []
        for i, (folded, entry) in enumerate(self._fr_fold):
            rank = self._rank(folded, q)
            if rank is not None:
                scored.append((rank, i, entry))
        scored.sort(key=lambda t: (t[0], len(t[2].fr), t[1]))
        return [e for _, _, e in scored[:limit]]

    def search_nko(self, query: str, limit: int) -> list[Entry]:
        q = query.strip()
        if not q:
            return []
        scored: list[tuple[int, int, Entry]] = []
        for i, entry in enumerate(self.entries):
            rank = self._rank(entry.nko, q)
            if rank is not None:
                scored.append((rank, i, entry))
        scored.sort(key=lambda t: (t[0], len(t[2].nko), t[1]))
        return [e for _, _, e in scored[:limit]]


def _load_entries(path: Path) -> list[Entry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Accept either {"entries": [...]} or a bare list.
    items = raw["entries"] if isinstance(raw, dict) else raw
    out: list[Entry] = []
    for it in items:
        fr = (it.get("fr") or "").strip()
        nko = (it.get("nko") or "").strip()
        if fr and nko:
            out.append(Entry(fr=fr, nko=nko, cat=(it.get("cat") or "").strip()))
    return out


@lru_cache(maxsize=1)
def get_dictionary() -> Dictionary:
    settings = get_settings()
    path = Path(settings.lexicon_path) if settings.lexicon_path else _SAMPLE_PATH
    if not path.exists():
        logger.warning("event=lexicon_missing path=%s falling_back_to_sample", path)
        path = _SAMPLE_PATH
    entries = _load_entries(path)
    logger.info("event=lexicon_loaded entries=%d path=%s", len(entries), path)
    return Dictionary(entries)
