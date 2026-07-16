"""Language-pack endpoints: multi-language ↔ N'Ko lookup (public, read-only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status

from app import langpack
from app.limits import limiter
from app.schemas import LangPackEntry, LangPackLanguage, LangPackResult

router = APIRouter(prefix="/api/langpack", tags=["langpack"])


@router.get("/languages", response_model=list[LangPackLanguage])
def languages():
    """List available language packs (code, display name, seed/full, size)."""
    return [
        LangPackLanguage(code=m.code, name=m.name, partial=m.partial, count=m.count)
        for m in langpack.available_languages()
    ]


@router.get("/lookup", response_model=LangPackResult)
@limiter.limit("60/minute")
def lookup(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    lang: str = Query(default="fr", max_length=8),
    dir: str = Query(default="term", pattern="^(term|nko)$"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Search a language pack: ``dir=term`` matches the source language
    (accent-insensitive), ``dir=nko`` matches the N'Ko side."""
    codes = {m.code for m in langpack.available_languages()}
    if lang not in codes:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown language {lang!r}; available: {', '.join(sorted(codes))}",
        )
    hits = langpack.search(lang, q, dir, limit)
    return LangPackResult(
        query=q,
        lang=lang,
        direction=dir,
        count=len(hits),
        entries=[LangPackEntry(term=e.fr, nko=e.nko, cat=e.cat) for e in hits],
    )
