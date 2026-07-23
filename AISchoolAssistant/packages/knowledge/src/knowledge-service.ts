import { supportsEmbeddings, type LanguageModelProvider } from '@asa/ai-sdk';
import { ValidationError } from '@asa/errors';
import type { VectorStore } from './vector-store';

/** A document to index into the knowledge base. */
export interface KnowledgeDocument {
  id: string;
  text: string;
  metadata?: Record<string, unknown>;
  tenantId?: string;
}

/** A search result: the matched document with its relevance score. */
export interface KnowledgeHit {
  id: string;
  score: number;
  text: string;
  metadata?: Record<string, unknown>;
}

/** Options for a knowledge search. */
export interface KnowledgeSearchOptions {
  topK?: number;
  tenantId?: string;
}

type EmbeddingProvider = LanguageModelProvider &
  Required<Pick<LanguageModelProvider, 'embed'>>;

/** Collaborators the knowledge service depends on. */
export interface KnowledgeServiceDeps {
  provider: LanguageModelProvider;
  store: VectorStore;
  /** Embedding model reference (`provider:model`). */
  model: string;
}

/**
 * The Knowledge Platform's ingestion + retrieval service. Documents are
 * embedded via the provider-agnostic AI SDK and stored in a {@link VectorStore};
 * search embeds the query and returns the nearest documents. Retrieval is
 * tenant-scoped end-to-end.
 */
export class KnowledgeService {
  private readonly provider: EmbeddingProvider;

  constructor(private readonly deps: KnowledgeServiceDeps) {
    if (!supportsEmbeddings(deps.provider)) {
      throw new ValidationError(
        `Provider "${deps.provider.id}" does not support embeddings.`,
      );
    }
    this.provider = deps.provider;
  }

  async ingest(documents: KnowledgeDocument[]): Promise<number> {
    if (documents.length === 0) {
      return 0;
    }
    const { embeddings } = await this.provider.embed({
      model: this.deps.model,
      input: documents.map((d) => d.text),
    });
    await this.deps.store.upsert(
      documents.map((doc, index) => ({
        id: doc.id,
        vector: embeddings[index],
        payload: { text: doc.text, metadata: doc.metadata ?? {} },
        tenantId: doc.tenantId,
      })),
    );
    return documents.length;
  }

  async search(
    query: string,
    options: KnowledgeSearchOptions = {},
  ): Promise<KnowledgeHit[]> {
    const { embeddings } = await this.provider.embed({
      model: this.deps.model,
      input: [query],
    });
    const matches = await this.deps.store.query({
      vector: embeddings[0],
      topK: options.topK ?? 5,
      tenantId: options.tenantId,
    });
    return matches.map((match) => ({
      id: match.id,
      score: match.score,
      text: String(match.payload.text ?? ''),
      metadata: match.payload.metadata as Record<string, unknown> | undefined,
    }));
  }
}
