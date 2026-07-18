"""Transliteration, lexicon search, and catalog endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.catalog import ENGINES, LANGUAGES
from app.nko import transliterate
from app.retrieval import get_retriever

router = APIRouter(tags=["tools"])


class TransliterateRequest(BaseModel):
    text: str = Field(max_length=20_000)


@router.post("/transliterate")
def transliterate_text(body: TransliterateRequest):
    return {"latin_text": body.text, "nko_text": transliterate(body.text)}


@router.get("/lexicon/search")
def lexicon_search(
    q: str = Query(min_length=1, max_length=200),
    direction: str = Query("fr"),
    limit: int = Query(10, ge=1, le=50),
):
    if direction not in {"fr", "nko"}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "direction must be fr|nko")
    return {"results": get_retriever().search(q, direction, limit)}


@router.get("/languages")
def languages():
    return {"languages": LANGUAGES}


@router.get("/asr/engines")
def engines():
    return {"engines": ENGINES}
