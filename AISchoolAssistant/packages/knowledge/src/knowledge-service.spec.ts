import { EchoProvider } from '@asa/ai-sdk';
import { ValidationError } from '@asa/errors';
import { KnowledgeService } from './knowledge-service';
import { InMemoryVectorStore } from './vector-store';

function service() {
  return new KnowledgeService({
    provider: new EchoProvider(),
    store: new InMemoryVectorStore(),
    model: 'echo:default',
  });
}

describe('KnowledgeService', () => {
  it('rejects a provider without embedding support', () => {
    const noEmbed = {
      id: 'noembed',
      generate: async () => ({
        text: '',
        finishReason: 'stop' as const,
        usage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
        model: 'x',
      }),
    };
    expect(
      () =>
        new KnowledgeService({
          provider: noEmbed,
          store: new InMemoryVectorStore(),
          model: 'x:y',
        }),
    ).toThrow(ValidationError);
  });

  it('ingests documents and returns the count', async () => {
    const svc = service();
    const count = await svc.ingest([
      { id: '1', text: 'algebra basics' },
      { id: '2', text: 'photosynthesis in plants' },
    ]);
    expect(count).toBe(2);
  });

  it('retrieves the most similar document for a query', async () => {
    const svc = service();
    await svc.ingest([
      { id: 'algebra', text: 'algebra equations and variables' },
      { id: 'biology', text: 'cells and photosynthesis' },
    ]);
    const hits = await svc.search('algebra equations and variables', {
      topK: 1,
    });
    expect(hits).toHaveLength(1);
    expect(hits[0].id).toBe('algebra');
    expect(hits[0].text).toContain('algebra');
    expect(hits[0].score).toBeGreaterThan(0);
  });

  it('scopes search to a tenant', async () => {
    const svc = service();
    await svc.ingest([
      { id: 'a', text: 'shared topic', tenantId: 't1' },
      { id: 'b', text: 'shared topic', tenantId: 't2' },
    ]);
    const hits = await svc.search('shared topic', { tenantId: 't1', topK: 5 });
    expect(hits.map((h) => h.id)).toEqual(['a']);
  });

  it('ingesting nothing is a no-op', async () => {
    expect(await service().ingest([])).toBe(0);
  });
});
