import { describe, expect, it } from 'vitest';
import { supportsEmbeddings, supportsStreaming } from '../provider';
import { EchoProvider } from './echo-provider';

const request = {
  model: 'echo:default',
  messages: [
    { role: 'system' as const, content: 'You are helpful.' },
    { role: 'user' as const, content: 'hello world' },
  ],
};

describe('EchoProvider', () => {
  const provider = new EchoProvider();

  it('advertises streaming and embedding support', () => {
    expect(supportsStreaming(provider)).toBe(true);
    expect(supportsEmbeddings(provider)).toBe(true);
  });

  it('echoes the last user message', async () => {
    const result = await provider.generate(request);
    expect(result.text).toBe('[echo] hello world');
    expect(result.finishReason).toBe('stop');
    expect(result.model).toBe('echo:default');
  });

  it('returns a JSON body when json format is requested', async () => {
    const result = await provider.generate({
      ...request,
      responseFormat: 'json',
    });
    expect(JSON.parse(result.text)).toEqual({ echo: 'hello world' });
  });

  it('reports non-zero, additive token usage', async () => {
    const result = await provider.generate(request);
    expect(result.usage.promptTokens).toBeGreaterThan(0);
    expect(result.usage.completionTokens).toBeGreaterThan(0);
    expect(result.usage.totalTokens).toBe(
      result.usage.promptTokens + result.usage.completionTokens,
    );
  });

  it('streams the full text across chunks', async () => {
    const chunks: string[] = [];
    let finishedOnce = false;
    for await (const chunk of provider.stream(request)) {
      chunks.push(chunk.delta);
      if (chunk.finishReason === 'stop') {
        finishedOnce = true;
      }
    }
    expect(chunks.join('')).toBe('[echo] hello world');
    expect(finishedOnce).toBe(true);
  });

  it('produces deterministic, normalized embeddings', async () => {
    const a = await provider.embed({ model: 'echo:default', input: ['abc'] });
    const b = await provider.embed({ model: 'echo:default', input: ['abc'] });
    expect(a.embeddings[0]).toEqual(b.embeddings[0]);
    const magnitude = Math.sqrt(a.embeddings[0].reduce((s, v) => s + v * v, 0));
    expect(magnitude).toBeCloseTo(1, 5);
  });
});
