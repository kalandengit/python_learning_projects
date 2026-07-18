"""Hybrid retrieval: dense (mistral-embed) + sparse (BM25) fused with RRF."""

from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import models

from app.config import settings
from app.ingestion.indexer import (
    DENSE,
    SPARSE,
    _bm25,
    embed_dense,
    ensure_collection,
    get_qdrant,
)


@dataclass
class RetrievedChunk:
    text: str
    source_file: str
    domain: str
    score: float


def retrieve(query: str, domain: str | None = None) -> list[RetrievedChunk]:
    """Return the most relevant chunks for a query, optionally filtered by domain."""
    ensure_collection()

    flt = None
    if domain and domain != "all":
        flt = models.Filter(
            must=[models.FieldCondition(key="domain", match=models.MatchValue(value=domain))]
        )

    dense_vec = embed_dense([query])[0]
    sparse_vec = next(iter(_bm25().query_embed(query)))
    candidates = settings.retrieve_candidates

    result = get_qdrant().query_points(
        collection_name=settings.qdrant_collection,
        prefetch=[
            models.Prefetch(query=dense_vec, using=DENSE, limit=candidates, filter=flt),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vec.indices.tolist(),
                    values=sparse_vec.values.tolist(),
                ),
                using=SPARSE,
                limit=candidates,
                filter=flt,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=settings.context_chunks,
        with_payload=True,
    )
    return [
        RetrievedChunk(
            text=p.payload["text"],
            source_file=p.payload["source_file"],
            domain=p.payload.get("domain", "general"),
            score=p.score,
        )
        for p in result.points
        if p.payload
    ]
