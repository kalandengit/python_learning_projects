import { ConflictError, ValidationError } from '@asa/errors';
import { CapabilityExecutor } from './capability-executor';
import { CapabilityRegistry } from './capability-registry';
import { InMemoryObservabilitySink } from './observability';
import { faqCapability, testDeps } from './testing/fixtures';

async function setup() {
  const registry = new CapabilityRegistry();
  const deps = testDeps();
  const sink = new InMemoryObservabilitySink();
  const executor = new CapabilityExecutor({
    registry,
    providers: deps.providers,
    router: deps.router,
    sink,
  });
  return { registry, deps, sink, executor };
}

describe('CapabilityExecutor', () => {
  it('refuses to invoke an unpublished capability', async () => {
    const { registry, executor } = await setup();
    registry.register(faqCapability());
    await expect(
      executor.invoke('faq-answer', '1.0.0', { question: 'hi' }),
    ).rejects.toBeInstanceOf(ConflictError);
  });

  it('invokes a published capability and records a success event', async () => {
    const { registry, deps, sink, executor } = await setup();
    await registry.registerAndPublish(faqCapability(), deps);

    const outcome = await executor.invoke(
      'faq-answer',
      '1.0.0',
      {
        question: 'hi',
      },
      { tenantId: 't-1', actor: 'user-1', correlationId: 'cid-1' },
    );

    expect(outcome.output).toEqual({ answer: '[echo] hi' });
    // The success event was published to the observability sink (draft eval
    // runs are not recorded — only executor invocations).
    const success = sink.events.filter((e) => e.success);
    expect(success).toHaveLength(1);
    expect(success[0]).toMatchObject({
      capabilityId: 'faq-answer',
      model: 'echo:default',
      tenantId: 't-1',
      actor: 'user-1',
      correlationId: 'cid-1',
    });
    expect(success[0].usage?.totalTokens).toBeGreaterThan(0);
  });

  it('records a failure event and rethrows on invalid input', async () => {
    const { registry, deps, sink, executor } = await setup();
    await registry.registerAndPublish(faqCapability(), deps);

    await expect(
      executor.invoke('faq-answer', '1.0.0', { question: '' }),
    ).rejects.toBeInstanceOf(ValidationError);

    const failure = sink.events.find((e) => !e.success);
    expect(failure).toMatchObject({
      capabilityId: 'faq-answer',
      success: false,
      errorCode: 'validation_error',
    });
  });
});
