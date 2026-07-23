import { ConflictError, NotFoundError } from '@asa/errors';
import { AgentRegistry } from './agent';
import { assistantAgent } from './testing/fixtures';

describe('AgentRegistry', () => {
  it('registers and resolves agents', () => {
    const registry = new AgentRegistry([assistantAgent()]);
    expect(registry.get('assistant', '1.0.0').tools).toEqual(['add']);
    expect(registry.list()).toEqual([{ id: 'assistant', version: '1.0.0' }]);
  });

  it('rejects duplicate id+version', () => {
    const registry = new AgentRegistry([assistantAgent()]);
    expect(() => registry.register(assistantAgent())).toThrow(ConflictError);
  });

  it('rejects an agent with maxSteps < 1', () => {
    expect(() =>
      new AgentRegistry().register(assistantAgent({ maxSteps: 0 })),
    ).toThrow(ConflictError);
  });

  it('throws NotFoundError for unknown agents', () => {
    expect(() => new AgentRegistry().get('nope', '1.0.0')).toThrow(
      NotFoundError,
    );
  });
});
