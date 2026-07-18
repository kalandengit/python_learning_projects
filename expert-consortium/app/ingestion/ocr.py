"""Text extraction from PDFs and images via Mistral OCR."""

from __future__ import annotations

import base64
from pathlib import Path

from app.config import settings
from app.mistral_client import get_client, with_retry

IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
}


def extract_pdf(path: Path) -> str:
    """OCR a PDF; returns markdown text with page breaks."""
    b64 = base64.b64encode(path.read_bytes()).decode()
    resp = with_retry(
        get_client().ocr.process,
        model=settings.ocr_model,
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64}",
        },
    )
    return "\n\n".join(page.markdown for page in resp.pages)


def extract_image(path: Path) -> str:
    """OCR a single image (photo of a page, scan, screenshot)."""
    mime = IMAGE_MIME[path.suffix.lower()]
    b64 = base64.b64encode(path.read_bytes()).decode()
    resp = with_retry(
        get_client().ocr.process,
        model=settings.ocr_model,
        document={"type": "image_url", "image_url": f"data:{mime};base64,{b64}"},
    )
    return "\n\n".join(page.markdown for page in resp.pages)
