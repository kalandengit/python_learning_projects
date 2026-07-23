import { describe, expect, it } from 'vitest';
import { ScriptedProvider } from './scripted-provider';

const request = {
  model: 'scripted:test',
  messages: [{ role: 'user' as const, content: 'go' }],
};

describe('ScriptedProvider', () => {
  it('returns scripted responses in order', async () => {
    const provider = new ScriptedProvider([
      { text: 'first' },
      { text: 'second' },
    ]);
    expect((await provider.generate(request)).text).toBe('first');
    expect((await provider.generate(request)).text).toBe('second');
    expect(provider.calls).toBe(2);
  });

  it('infers tool_calls finish reason when tool calls are present', async () => {
    const provider = new ScriptedProvider([
      { toolCalls: [{ id: '1', name: 'calc', arguments: '{}' }] },
    ]);
    const result = await provider.generate(request);
    expect(result.finishReason).toBe('tool_calls');
    expect(result.toolCalls).toHaveLength(1);
  });

  it('defaults to a stop finish reason for a text turn', async () => {
    const provider = new ScriptedProvider([{ text: 'done' }]);
    expect((await provider.generate(request)).finishReason).toBe('stop');
  });

  it('throws once the script is exhausted', async () => {
    const provider = new ScriptedProvider([{ text: 'only' }]);
    await provider.generate(request);
    await expect(provider.generate(request)).rejects.toThrow(/exhausted/);
  });
});
