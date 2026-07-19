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


def _check_size(path: Path) -> None:
    size_mb = path.stat().st_size / 1_000_000
    if size_mb > settings.max_ocr_mb:
        raise ValueError(
            f"{path.name} is {size_mb:.0f} MB — above the OCR limit "
            f"({settings.max_ocr_mb} MB). Split the PDF into parts (e.g. with "
            f"'pdftk {path.name} burst' or an online splitter) and upload the parts."
        )


def extract_pdf(path: Path) -> str:
    """OCR a PDF; returns markdown text with page breaks."""
    _check_size(path)
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
    _check_size(path)
    mime = IMAGE_MIME[path.suffix.lower()]
    b64 = base64.b64encode(path.read_bytes()).decode()
    resp = with_retry(
        get_client().ocr.process,
        model=settings.ocr_model,
        document={"type": "image_url", "image_url": f"data:{mime};base64,{b64}"},
    )
    return "\n\n".join(page.markdown for page in resp.pages)
