"""N'Ko ↔ French dictionary lookup endpoint (read-only, public)."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.dictionary import get_dictionary
from app.limits import limiter
from app.schemas import DictionaryEntry, DictionaryResult

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])


@router.get("", response_model=DictionaryResult)
@limiter.limit("60/minute")
def lookup(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    dir: str = Query(default="fr", pattern="^(fr|nko)$"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Search the lexicon. ``dir=fr`` matches French headwords (accent-
    insensitive); ``dir=nko`` matches the N'Ko side."""
    dictionary = get_dictionary()
    hits = dictionary.search_fr(q, limit) if dir == "fr" else dictionary.search_nko(q, limit)
    return DictionaryResult(
        query=q,
        direction=dir,
        count=len(hits),
        entries=[DictionaryEntry(fr=e.fr, nko=e.nko, cat=e.cat) for e in hits],
    )
