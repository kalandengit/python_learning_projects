import { ValidationError } from '@asa/errors';

/** A stored vector record with an opaque payload. */
export interface VectorRecord {
  id: string;
  vector: number[];
  payload: Record<string, unknown>;
  /** Tenant that owns the record (isolation boundary). */
  tenantId?: string;
}

/** A scored search hit. */
export interface VectorMatch {
  id: string;
  score: number;
  payload: Record<string, unknown>;
}

/** Options for a similarity query. */
export interface VectorQuery {
  vector: number[];
  topK: number;
  /** Restrict results to a tenant. */
  tenantId?: string;
}

/**
 * The vector-store port. Business code depends only on this interface — never a
 * vector-DB SDK — so the in-memory store (dev/test) and a Qdrant adapter
 * (production) are interchangeable.
 */
export interface VectorStore {
  upsert(records: VectorRecord[]): Promise<void>;
  query(query: VectorQuery): Promise<VectorMatch[]>;
  clear(): Promise<void>;
}

/** Cosine similarity of two equal-length vectors, in [-1, 1]. */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new ValidationError('Vectors must have the same dimensionality.');
  }
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}

/**
 * In-memory vector store using exact cosine similarity. Deterministic and
 * dependency-free — ideal for tests and local development. Tenant-scoped so a
 * query never crosses the isolation boundary.
 */
export class InMemoryVectorStore implements VectorStore {
  private readonly records = new Map<string, VectorRecord>();

  async upsert(records: VectorRecord[]): Promise<void> {
    for (const record of records) {
      this.records.set(record.id, record);
    }
  }

  async query(query: VectorQuery): Promise<VectorMatch[]> {
    const candidates = [...this.records.values()].filter(
      (r) => query.tenantId === undefined || r.tenantId === query.tenantId,
    );
    return candidates
      .map((record) => ({
        id: record.id,
        score: cosineSimilarity(query.vector, record.vector),
        payload: record.payload,
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, Math.max(0, query.topK));
  }

  async clear(): Promise<void> {
    this.records.clear();
  }
}
