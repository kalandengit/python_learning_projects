"""FastAPI web application: password-protected chat UI + JSON API."""

from __future__ import annotations

import secrets
import time
from collections import defaultdict
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import DOMAINS, settings, setup_logging
from app.ingestion import indexer, router as ingest_router
from app.rag import chat as rag_chat

logger = setup_logging()
app = FastAPI(title="Expert Consortium", version="1.0.0", docs_url=None, redoc_url=None)

STATIC_DIR = Path(__file__).parent / "static"

# --- Auth: shared password in the X-Password header, brute-force throttled ---

_failed: dict[str, list[float]] = defaultdict(list)
_WINDOW, _MAX_FAILURES = 300.0, 10


def check_password(x_password: str = Header(default="")) -> None:
    now = time.monotonic()
    attempts = _failed["global"]
    attempts[:] = [t for t in attempts if now - t < _WINDOW]
    if len(attempts) >= _MAX_FAILURES:
        raise HTTPException(429, "Too many failed attempts, wait 5 minutes.")
    if not secrets.compare_digest(x_password, settings.web_password):
        attempts.append(now)
        raise HTTPException(401, "Wrong password.")


# --- Schemas ---


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    domain: str = "all"
    history: list[dict] = Field(default_factory=list, max_length=24)


class RateRequest(BaseModel):
    log_ts: str
    rating: str = Field(pattern="^(good|bad)$")


# --- Routes ---


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/login", dependencies=[Depends(check_password)])
def login() -> dict:
    return {"ok": True}


@app.post("/api/chat", dependencies=[Depends(check_password)])
def api_chat(req: ChatRequest) -> dict:
    domain = req.domain if req.domain in DOMAINS else None
    try:
        result = rag_chat.ask(req.question, domain=domain, history=req.history)
    except Exception as exc:  # surfaces as a readable message in the UI
        logger.exception("Chat failed")
        raise HTTPException(502, f"The assistant could not answer: {exc}") from exc
    return {"answer": result.answer, "sources": result.sources, "log_ts": result.log_ts}


@app.post("/api/rate", dependencies=[Depends(check_password)])
def api_rate(req: RateRequest) -> dict:
    return {"updated": rag_chat.rate_exchange(req.log_ts, req.rating)}


@app.post("/api/upload", dependencies=[Depends(check_password)])
async def api_upload(file: UploadFile = File(...), domain: str = Form("general")) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(400, f"Unknown domain '{domain}'.")
    name = Path(file.filename or "upload").name  # strip any path components
    if Path(name).suffix.lower() not in ingest_router.SUPPORTED_EXTS:
        raise HTTPException(
            400,
            f"Unsupported file type. Supported: "
            f"{', '.join(sorted(ingest_router.SUPPORTED_EXTS))}",
        )
    target_dir = settings.uploads_dir / (domain if domain != "general" else "")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / name
    target.write_bytes(await file.read())

    try:
        doc = ingest_router.extract(target, domain=domain)  # type: ignore[arg-type]
        n_chunks = indexer.index_document(doc)
    except Exception as exc:
        logger.exception("Ingestion failed for %s", name)
        raise HTTPException(422, f"Could not ingest {name}: {exc}") from exc
    return {"file": name, "chunks": n_chunks, "domain": doc.domain, "language": doc.language}


@app.get("/api/documents", dependencies=[Depends(check_password)])
def api_documents() -> list[dict]:
    return indexer.list_documents()


@app.delete("/api/documents/{name}", dependencies=[Depends(check_password)])
def api_delete_document(name: str) -> dict:
    indexer.delete_document(Path(name).name)
    return {"deleted": name}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
