"""N'Ko alphabet reference endpoint (public, static teaching data)."""

from __future__ import annotations

from fastapi import APIRouter

from app.nko import block
from app.schemas import AlphabetEntry

router = APIRouter(prefix="/api/alphabet", tags=["reference"])


@router.get("", response_model=list[AlphabetEntry])
def alphabet():
    """The full N'Ko block as an ordered teaching table: glyph, name, Latin
    value, and kind (letter/digit/mark/symbol)."""
    return [AlphabetEntry(**e) for e in block.alphabet()]
