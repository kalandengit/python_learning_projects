import { EchoProvider, ScriptedProvider } from '@asa/ai-sdk';
import { ForbiddenError, ValidationError } from '@asa/errors';
import { makeExecutor } from './testing/fixtures';

const toolCall = (args: string) => ({
  toolCalls: [{ id: '1', name: 'add', arguments: args }],
});

describe('AgentExecutor', () => {
  it('completes in a single step when the model needs no tools', async () => {
    const { executor, sink } = makeExecutor(new EchoProvider());
    const result = await executor.run('assistant', '1.0.0', {
      goal: 'say hi',
    });
    expect(result.finishReason).toBe('completed');
    expect(result.steps).toBe(1);
    expect(result.output).toBe('[echo] say hi');
    expect(result.toolsUsed).toEqual([]);
    expect(sink.events[0]).toMatchObject({ success: true, steps: 1 });
  });

  it('runs a tool call then returns the final answer', async () => {
    const provider = new ScriptedProvider([
      toolCall('{"a":2,"b":3}'),
      { text: 'The sum is 5.' },
    ]);
    const { executor, sink } = makeExecutor(provider);

    const result = await executor.run(
      'assistant',
      '1.0.0',
      { goal: 'add 2 and 3' },
      { tenantId: 't-1', actor: 'user-1', correlationId: 'cid-1' },
    );

    expect(result.output).toBe('The sum is 5.');
    expect(result.steps).toBe(2);
    expect(result.toolsUsed).toEqual(['add']);
    expect(result.finishReason).toBe('completed');
    expect(sink.events[0]).toMatchObject({
      success: true,
      toolsUsed: ['add'],
      tenantId: 't-1',
      actor: 'user-1',
      correlationId: 'cid-1',
    });
  });

  it('stops at maxSteps when the model keeps calling tools', async () => {
    const provider = new ScriptedProvider([
      toolCall('{"a":1,"b":1}'),
      toolCall('{"a":1,"b":1}'),
    ]);
    const { executor, sink } = makeExecutor(provider, { maxSteps: 2 });

    const result = await executor.run('assistant', '1.0.0', { goal: 'loop' });
    expect(result.finishReason).toBe('max_steps');
    expect(result.steps).toBe(2);
    expect(result.toolsUsed).toEqual(['add', 'add']);
    expect(sink.events[0]).toMatchObject({ finishReason: 'max_steps' });
  });

  it('forbids a tool the agent is not allowed to use', async () => {
    const provider = new ScriptedProvider([
      { toolCalls: [{ id: '1', name: 'delete', arguments: '{}' }] },
    ]);
    const { executor, sink } = makeExecutor(provider);
    await expect(
      executor.run('assistant', '1.0.0', { goal: 'x' }),
    ).rejects.toBeInstanceOf(ForbiddenError);
    expect(sink.events[0]).toMatchObject({ success: false });
  });

  it('rejects invalid tool arguments and records a failure', async () => {
    const provider = new ScriptedProvider([toolCall('{"a":"nope","b":3}')]);
    const { executor, sink } = makeExecutor(provider);
    await expect(
      executor.run('assistant', '1.0.0', { goal: 'x' }),
    ).rejects.toBeInstanceOf(ValidationError);
    expect(sink.events[0]).toMatchObject({
      success: false,
      errorCode: 'validation_error',
    });
  });

  it('rejects malformed JSON tool arguments', async () => {
    const provider = new ScriptedProvider([toolCall('not-json')]);
    const { executor } = makeExecutor(provider);
    await expect(
      executor.run('assistant', '1.0.0', { goal: 'x' }),
    ).rejects.toBeInstanceOf(ValidationError);
  });

  it('enforces the model governance allow-list', async () => {
    const provider = new ScriptedProvider([{ text: 'hi' }]);
    const { executor } = makeExecutor(provider, {
      governance: {
        owner: 'x',
        dataClassification: 'internal',
        pii: false,
        modelAllowList: [],
      },
    });
    await expect(
      executor.run('assistant', '1.0.0', { goal: 'x' }),
    ).rejects.toBeInstanceOf(ForbiddenError);
  });
});
