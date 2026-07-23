# @asa/knowledge

The Knowledge Platform (ADR-0007): a transport-agnostic vector store and an
embedding-backed knowledge service built on `@asa/ai-sdk`.

## Concepts

- **`VectorStore`** — the port for vector upsert + similarity query. Business
  code never imports a vector-DB SDK. `InMemoryVectorStore` (exact cosine,
  tenant-scoped) serves dev/test; a Qdrant adapter is the production drop-in.
- **`KnowledgeService`** — embeds documents via the provider-agnostic AI SDK and
  upserts them; `search` embeds the query and returns the nearest documents.
  Ingestion and retrieval are **tenant-scoped** end-to-end.

## Usage

```ts
KnowledgeModule.forRoot({
  provider: new EchoProvider(), // default; swap for a real embedding provider
  model: 'echo:default',
  // store: new QdrantVectorStore(...) in production
});

await knowledge.ingest([{ id: 'doc-1', text: '...', tenantId }]);
const hits = await knowledge.search('query', { topK: 5, tenantId });
```

## Testing

`InMemoryVectorStore` + the deterministic `EchoProvider` embeddings make ranking
reproducible: ingest documents and assert the expected hit ordering, with no
network or vector database.
