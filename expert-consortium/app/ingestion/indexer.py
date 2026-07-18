"""Index Documents into Qdrant with hybrid vectors (mistral-embed dense + BM25 sparse)."""

from __future__ import annotations

import atexit
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.config import setup_logging, settings
from app.ingestion.chunker import chunk_text
from app.ingestion.router import Document
from app.mistral_client import get_client, with_retry

logger = setup_logging()

DENSE = "dense"
SPARSE = "bm25"
DENSE_DIM = 1024  # mistral-embed output size
_BM25_MODEL = "Qdrant/bm25"
_EMBED_BATCH = 64


@lru_cache(maxsize=1)
def get_qdrant() -> QdrantClient:
    if settings.qdrant_url:
        client = QdrantClient(url=settings.qdrant_url)
    else:
        path = settings.data_dir / "qdrant"
        path.mkdir(parents=True, exist_ok=True)
        try:
            client = QdrantClient(path=str(path))
        except RuntimeError as exc:
            if "already accessed" in str(exc).lower():
                raise RuntimeError(
                    "The local knowledge base is already open in another process "
                    "(e.g. the web app AND the Telegram bot at the same time). "
                    "Embedded storage allows only ONE process. Either stop the other "
                    "process, or run a Qdrant server and set QDRANT_URL in .env — "
                    "docker compose does this automatically (docs/en/10-limits.md)."
                ) from exc
            raise
    # Close before interpreter teardown; __del__ at shutdown prints scary noise.
    atexit.register(client.close)
    return client


@lru_cache(maxsize=1)
def _bm25():
    from fastembed import SparseTextEmbedding

    return SparseTextEmbedding(model_name=_BM25_MODEL)


def ensure_collection() -> None:
    client = get_qdrant()
    if client.collection_exists(settings.qdrant_collection):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config={
            DENSE: models.VectorParams(size=DENSE_DIM, distance=models.Distance.COSINE)
        },
        sparse_vectors_config={
            SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    if settings.qdrant_url:  # payload indexes only apply to server Qdrant
        client.create_payload_index(
            settings.qdrant_collection, "source_file", models.PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            settings.qdrant_collection, "domain", models.PayloadSchemaType.KEYWORD
        )


def _embed_batches(texts: list[str]) -> list[list[str]]:
    """Group texts into batches bounded by count AND total characters, so one
    request never exceeds the embeddings API token limit on huge documents."""
    batches: list[list[str]] = []
    current: list[str] = []
    chars = 0
    for text in texts:
        if current and (
            len(current) >= _EMBED_BATCH
            or chars + len(text) > settings.embed_batch_char_budget
        ):
            batches.append(current)
            current, chars = [], 0
        current.append(text)
        chars += len(text)
    if current:
        batches.append(current)
    return batches


def embed_dense(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for batch in _embed_batches(texts):
        resp = with_retry(
            get_client().embeddings.create, model=settings.embed_model, inputs=batch
        )
        out.extend(item.embedding for item in resp.data)
    return out


def _point_id(source_file: str, chunk_index: int) -> str:
    """Deterministic id: re-ingesting a file overwrites its previous chunks."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_file}#{chunk_index}"))


def delete_document(source_file: str) -> None:
    get_qdrant().delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_file",
                        match=models.MatchValue(value=source_file),
                    )
                ]
            )
        ),
    )


def index_document(doc: Document) -> int:
    """Chunk, embed, and upsert one document. Returns the number of chunks indexed."""
    ensure_collection()
    chunks = chunk_text(doc.text)
    if not chunks:
        return 0

    dense_vectors = embed_dense(chunks)
    sparse_vectors = list(_bm25().embed(chunks))

    # Remove stale chunks first (e.g. shorter re-upload of the same file).
    delete_document(doc.source_file)

    points = [
        models.PointStruct(
            id=_point_id(doc.source_file, i),
            vector={
                DENSE: dense,
                SPARSE: models.SparseVector(
                    indices=sparse.indices.tolist(), values=sparse.values.tolist()
                ),
            },
            payload={
                "text": chunk,
                "source_file": doc.source_file,
                "domain": doc.domain,
                "language": doc.language,
                "ingested_at": doc.ingested_at,
                "chunk_index": i,
            },
        )
        for i, (chunk, dense, sparse) in enumerate(
            zip(chunks, dense_vectors, sparse_vectors)
        )
    ]
    get_qdrant().upsert(collection_name=settings.qdrant_collection, points=points)
    logger.info("Indexed %s: %d chunks (domain=%s)", doc.source_file, len(points), doc.domain)
    return len(points)


def list_documents() -> list[dict]:
    """Distinct indexed files with chunk counts and metadata (for UI/CLI listing)."""
    ensure_collection()
    docs: dict[str, dict] = {}
    offset = None
    while True:
        points, offset = get_qdrant().scroll(
            collection_name=settings.qdrant_collection,
            limit=256,
            offset=offset,
            with_payload=["source_file", "domain", "language", "ingested_at"],
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            name = payload.get("source_file", "?")
            entry = docs.setdefault(
                name,
                {"source_file": name, "chunks": 0,
                 "domain": payload.get("domain"),
                 "language": payload.get("language"),
                 "ingested_at": payload.get("ingested_at")},
            )
            entry["chunks"] += 1
        if offset is None:
            break
    return sorted(docs.values(), key=lambda d: d["source_file"])
