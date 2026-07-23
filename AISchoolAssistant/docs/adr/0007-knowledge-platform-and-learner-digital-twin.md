# ADR-0007: Knowledge Platform + Learner Digital Twin

- **Status:** Accepted
- **Date:** 2026-07-23
- **Context:** Master Spec #7 (Knowledge Platform), #8 (Learner Digital Twin);
  builds on ADR-0002 (AI SDK) and ADR-0006 (eventing); WP-4.

## Decision

### Knowledge Platform (`@asa/knowledge`)

1. **Vector-store port** — business code depends on a `VectorStore` interface,
   never a vector-DB SDK. `InMemoryVectorStore` (exact cosine) serves dev/test; a
   **Qdrant** adapter is the production implementation (deferred, drop-in).
2. **KnowledgeService** — embeds documents via the provider-agnostic AI SDK
   (ADR-0002) and upserts them; search embeds the query and returns the nearest
   documents. Ingestion and retrieval are **tenant-scoped** end-to-end.

### Learner Digital Twin

3. Modeled as an **event-sourced projection** (ADR-0006): the twin
   (`lessonsCompleted`, `assessmentsTaken`, `averageScore`, `masteryByTopic`) is
   derived by subscribing to learner domain events on the bus — never written
   directly. This makes the twin reproducible, auditable, and decoupled from the
   producers of learning activity.

## Motivation

- The vector-store port keeps retrieval-augmented features portable across
  vector databases and testable offline (deterministic embeddings + exact
  cosine).
- Event sourcing the twin means any service can contribute activity (LMS, SIS,
  assessments) without coupling to the twin, and the projection can be rebuilt
  from the event log.
- Tenant scoping at the store and query level enforces isolation for both
  knowledge and learner data.

## Rules (enforced)

- Knowledge queries never cross the tenant boundary (store filters by tenant).
- The Digital Twin is updated only by event projection; the read model is not
  mutated by request handlers.
- Embeddings flow through the AI SDK (no direct provider calls).

## Alternatives considered

- **Direct DB reads/writes for the twin** — rejected: couples every producer to
  the twin schema, loses the audit trail and rebuildability.
- **Keyword search instead of vectors** — rejected for semantic retrieval; a
  lexical index (OpenSearch) is complementary and added alongside Qdrant later.

## Consequences

- `@asa/knowledge` ships the vector-store port + in-memory store, the knowledge
  service, and a NestJS `KnowledgeModule`. The service template exposes
  ingest/search endpoints and a Learner Digital Twin (record activity → events →
  projection → read).
- Qdrant + OpenSearch adapters, chunking, and re-ranking land with the
  production data stores in a later WP. Capability-backed RAG (a capability that
  retrieves from the Knowledge Platform) composes ADR-0002 with this ADR.
