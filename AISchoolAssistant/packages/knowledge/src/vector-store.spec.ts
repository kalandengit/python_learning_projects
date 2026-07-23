import { ValidationError } from '@asa/errors';
import { InMemoryVectorStore, cosineSimilarity } from './vector-store';

describe('cosineSimilarity', () => {
  it('is 1 for identical directions', () => {
    expect(cosineSimilarity([1, 0], [2, 0])).toBeCloseTo(1, 6);
  });

  it('is 0 for orthogonal vectors', () => {
    expect(cosineSimilarity([1, 0], [0, 1])).toBeCloseTo(0, 6);
  });

  it('is 0 when a vector is all zeros', () => {
    expect(cosineSimilarity([0, 0], [1, 1])).toBe(0);
  });

  it('rejects mismatched dimensions', () => {
    expect(() => cosineSimilarity([1], [1, 2])).toThrow(ValidationError);
  });
});

describe('InMemoryVectorStore', () => {
  it('returns the nearest records ranked by similarity', async () => {
    const store = new InMemoryVectorStore();
    await store.upsert([
      { id: 'a', vector: [1, 0], payload: { t: 'a' } },
      { id: 'b', vector: [0, 1], payload: { t: 'b' } },
      { id: 'c', vector: [0.9, 0.1], payload: { t: 'c' } },
    ]);
    const matches = await store.query({ vector: [1, 0], topK: 2 });
    expect(matches.map((m) => m.id)).toEqual(['a', 'c']);
    expect(matches[0].score).toBeGreaterThan(matches[1].score);
  });

  it('upsert overwrites an existing id', async () => {
    const store = new InMemoryVectorStore();
    await store.upsert([{ id: 'a', vector: [1, 0], payload: { v: 1 } }]);
    await store.upsert([{ id: 'a', vector: [1, 0], payload: { v: 2 } }]);
    const matches = await store.query({ vector: [1, 0], topK: 5 });
    expect(matches).toHaveLength(1);
    expect(matches[0].payload.v).toBe(2);
  });

  it('scopes queries to a tenant', async () => {
    const store = new InMemoryVectorStore();
    await store.upsert([
      { id: 'a', vector: [1, 0], payload: {}, tenantId: 't1' },
      { id: 'b', vector: [1, 0], payload: {}, tenantId: 't2' },
    ]);
    const matches = await store.query({
      vector: [1, 0],
      topK: 5,
      tenantId: 't1',
    });
    expect(matches.map((m) => m.id)).toEqual(['a']);
  });
});
