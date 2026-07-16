"""Language-pack module.

A pluggable layer over the N'Ko dictionary: each *language pack* maps terms in
one language (French, English, Russian, Chinese, Arabic, …) to N'Ko. The full
French pack is the reference lexicon; the others are curated seed packs that
can be completed over time. Adding a language is a single JSON file in
``app/data/langpacks/`` — no code change.
"""

from app.langpack.registry import (
    LangPackMeta,
    available_languages,
    get_pack,
    search,
)

__all__ = ["LangPackMeta", "available_languages", "get_pack", "search"]
