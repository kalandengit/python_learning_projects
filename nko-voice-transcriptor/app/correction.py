"""Retrieval correction using human-approved transcript pairs."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TrainingSample

_GLOSSARY = Path(__file__).parent / "data" / "correction-glossary-bam.json"


@lru_cache
def _glossary() -> dict[str, str]:
    return json.loads(_GLOSSARY.read_text(encoding="utf-8"))


def dictionary_correct(text: str, language: str) -> str:
    """Apply reviewed Bambara phrase normalization without generative guessing."""
    if language != "bam":
        return text
    normalized = " ".join(text.casefold().split())
    return _glossary().get(normalized, text)


def retrieve_correction(text: str, language: str, db: Session) -> tuple[str, float]:
    """Return a close approved correction; conservative threshold prevents invention."""
    text = dictionary_correct(text, language)
    rows = db.scalars(
        select(TrainingSample)
        .where(TrainingSample.status == "approved", TrainingSample.language == language)
        .order_by(TrainingSample.reviewed_at.desc())
        .limit(500)
    )
    best_text, best_score = text, 0.0
    normalized = text.casefold().strip()
    for row in rows:
        if not row.corrected_text_latin:
            continue
        score = SequenceMatcher(None, normalized, row.raw_text_latin.casefold().strip()).ratio()
        if score > best_score:
            best_text, best_score = row.corrected_text_latin, score
    return (best_text, best_score) if best_score >= 0.92 else (text, best_score)
