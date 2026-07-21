"""Language-pack registry: discovery, loading, and cross-language lookup.

Each pack is a JSON file ``app/data/langpacks/<code>.json`` of the shape::

    {"_language": "en", "_name": "English", "_partial": true,
     "entries": [{"term": "water", "nko": "ߓߊߟߋ߲", "cat": "ߕ."}, ...]}

The French pack is special: it is the full reference lexicon served by
:mod:`app.dictionary`, so we don't duplicate ~47k entries here.

Search reuses the dictionary's ranking (exact → prefix → substring) and its
accent-insensitive folding, treating each pack entry's ``term`` as the source
word. This module is read-only; no user data is involved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.dictionary import Dictionary, Entry, get_dictionary
from app.logging_conf import get_logger
from app.nko import block

logger = get_logger(__name__)

_PACKS_DIR = Path(__file__).resolve().parent.parent / "data" / "langpacks"

# Display names / order for packs that may exist. French (the full lexicon) and
# Bambara (derived from it) are always present; the rest load if their JSON
# file exists.
_KNOWN = {
    "fr": "Français",
    "bm": "Bamanankan",
    "en": "English",
    "ru": "Русский",
    "zh": "中文",
    "ar": "العربية",
}

# N'Ko combining marks that have no Latin base letter: tone marks are dropped
# on romanization; the nasalization mark becomes an "n".
_NASALIZATION = 0x07F2


def _romanize_nko(text: str) -> str:
    """Approximate Bambara Latin form of an N'Ko string.

    Deterministic reverse of the transliterator's letter/digit table. Tone
    diacritics are dropped (they have no Latin letter); the nasalization mark
    becomes ``n``. The result is approximate Bambara orthography — good for
    lookup, not a substitute for a native speaker's spelling.
    """
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if ch.isspace():
            out.append(ch)
        elif cp == _NASALIZATION:
            out.append("n")
        elif 0x07EB <= cp <= 0x07F3:  # other combining marks → drop
            continue
        else:
            out.append(block.romanize(ch))
    return "".join(out).strip()


def _bambara_pack() -> Dictionary:
    """French-derived Bambara pack: romanize every lexicon N'Ko to Latin."""
    entries = [
        Entry(fr=_romanize_nko(e.nko), nko=e.nko, cat=e.cat)
        for e in get_dictionary().entries
    ]
    entries = [e for e in entries if e.fr]
    return Dictionary(entries)


@dataclass(frozen=True)
class LangPackMeta:
    code: str
    name: str
    partial: bool   # True = curated seed, False = full pack
    count: int


def _load_pack_file(path: Path) -> tuple[Dictionary, bool]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw["entries"] if isinstance(raw, dict) else raw
    partial = bool(raw.get("_partial", False)) if isinstance(raw, dict) else False
    entries = [
        Entry(fr=(it.get("term") or "").strip(), nko=(it.get("nko") or "").strip(),
              cat=(it.get("cat") or "").strip())
        for it in items
        if (it.get("term") and it.get("nko"))
    ]
    return Dictionary(entries), partial


@lru_cache(maxsize=1)
def _registry() -> dict[str, tuple[Dictionary, bool]]:
    """Map language code → (Dictionary, is_partial). Built once."""
    reg: dict[str, tuple[Dictionary, bool]] = {}
    # French = the full reference lexicon.
    reg["fr"] = (get_dictionary(), False)
    # Bambara = derived from the same lexicon by romanizing the N'Ko.
    reg["bm"] = (_bambara_pack(), False)
    if _PACKS_DIR.is_dir():
        for path in sorted(_PACKS_DIR.glob("*.json")):
            code = path.stem
            if code == "fr":
                continue  # never shadow the full French lexicon
            try:
                reg[code] = _load_pack_file(path)
            except Exception as exc:  # noqa: BLE001 - skip a broken pack, keep serving
                logger.warning("event=langpack_load_failed code=%s error=%s", code, exc)
    logger.info("event=langpacks_loaded codes=%s", ",".join(sorted(reg)))
    return reg


def available_languages() -> list[LangPackMeta]:
    """Metadata for every loaded pack, French first then alphabetical."""
    reg = _registry()
    order = ["fr"] + sorted(c for c in reg if c != "fr")
    out = []
    for code in order:
        dictionary, partial = reg[code]
        out.append(
            LangPackMeta(
                code=code,
                name=_KNOWN.get(code, code),
                partial=partial,
                count=len(dictionary),
            )
        )
    return out


def get_pack(code: str) -> Dictionary | None:
    entry = _registry().get(code)
    return entry[0] if entry else None


def search(lang: str, query: str, direction: str, limit: int) -> list[Entry]:
    """Look up ``query`` in the given language pack.

    ``direction`` is ``"term"`` (match the source language, accent-insensitive)
    or ``"nko"`` (match the N'Ko side).
    """
    dictionary = get_pack(lang)
    if dictionary is None:
        return []
    if direction == "nko":
        return dictionary.search_nko(query, limit)
    return dictionary.search_fr(query, limit)  # search_fr folds accents on `term`
