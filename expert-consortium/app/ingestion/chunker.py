"""Structure-aware chunking: split on headings/paragraphs, target size with overlap."""

from __future__ import annotations

import re

from app.config import settings

_HEADING = re.compile(r"^#{1,6} ", re.MULTILINE)


def _split_blocks(text: str) -> list[str]:
    """Split into heading-led sections, then paragraphs within oversized sections."""
    positions = [m.start() for m in _HEADING.finditer(text)] or [0]
    if positions[0] != 0:
        positions.insert(0, 0)
    sections = [
        text[start:end].strip()
        for start, end in zip(positions, positions[1:] + [len(text)])
    ]
    blocks: list[str] = []
    for section in sections:
        if len(section) <= settings.chunk_chars:
            if section:
                blocks.append(section)
        else:
            blocks.extend(p.strip() for p in section.split("\n\n") if p.strip())
    return blocks


def _split_long(block: str, limit: int) -> list[str]:
    """Last resort for a single block longer than the limit: cut at sentence ends."""
    pieces: list[str] = []
    while len(block) > limit:
        cut = max(
            block.rfind(". ", 0, limit),
            block.rfind("۔", 0, limit),  # Arabic full stop
            block.rfind("\n", 0, limit),
        )
        if cut <= 0:
            cut = limit
        pieces.append(block[: cut + 1].strip())
        block = block[cut + 1 :]
    if block.strip():
        pieces.append(block.strip())
    return pieces


def chunk_text(text: str) -> list[str]:
    """Assemble blocks into chunks of ~settings.chunk_chars with trailing overlap."""
    limit = settings.chunk_chars
    overlap = settings.chunk_overlap_chars

    # Long blocks are split with headroom so overlap + block still fits the limit.
    block_limit = limit - overlap - 2
    blocks: list[str] = []
    for block in _split_blocks(text):
        blocks.extend(_split_long(block, block_limit) if len(block) > block_limit else [block])

    chunks: list[str] = []
    current = ""
    for block in blocks:
        if current and len(current) + len(block) + 2 > limit:
            chunks.append(current)
            current = current[-overlap:] if overlap else ""
        current = f"{current}\n\n{block}".strip() if current else block
    if current:
        chunks.append(current)
    return chunks
