"""N'Ko ↔ French dictionary lookup.

Data originates from the NKo Wuruki / N'Ko Institute lexicon
(https://www.nkowuruki.net/lexique-nkofr.html) — see ``app/data/NOTICE.md``.
Lexicon selection, in priority order:

1. ``NKO_LEXICON_PATH`` if set (bring your own),
2. the bundled full French–N'Ko lexicon ``app/data/lexicon-fr-nko.json``
   (~47,800 entries),
3. the small ``app/data/lexicon-sample.json`` fallback.

Lookup is in-memory and case/accent-insensitive on the French side. Matches
are ranked exact → prefix → substring so the most relevant entries surface
first. This is a read-only feature: no user data is involved.
"""

from __future__ import annotations

import json
import secrets
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

_DATA_DIR = Path(__file__).parent / "data"
_FULL_PATH = _DATA_DIR / "lexicon-fr-nko.json"
_SAMPLE_PATH = _DATA_DIR / "lexicon-sample.json"


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

    def practice(self, limit: int = 10) -> list[Entry]:
        """Return varied, short entries suitable for listen-and-type practice."""
        suitable = [e for e in self.entries if len(e.fr) <= 40 and len(e.nko) <= 80]
        return secrets.SystemRandom().sample(suitable, min(limit, len(suitable)))


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


def _resolve_lexicon_path() -> Path:
    settings = get_settings()
    if settings.lexicon_path:
        path = Path(settings.lexicon_path)
        if path.exists():
            return path
        logger.warning("event=lexicon_missing path=%s falling_back", path)
    if _FULL_PATH.exists():
        return _FULL_PATH
    return _SAMPLE_PATH


@lru_cache(maxsize=1)
def get_dictionary() -> Dictionary:
    path = _resolve_lexicon_path()
    entries = _load_entries(path)
    logger.info("event=lexicon_loaded entries=%d path=%s", len(entries), path.name)
    return Dictionary(entries)
