import { ForbiddenError, InternalError, ValidationError } from '@asa/errors';
import { executeCapability } from './execution';
import { faqCapability, testDeps, FAQ_OUTPUT } from './testing/fixtures';

describe('executeCapability', () => {
  it('runs the governed path and returns typed output + telemetry', async () => {
    const outcome = await executeCapability(
      faqCapability(),
      { question: 'hello' },
      {},
      testDeps(),
    );
    expect(outcome.output).toEqual({ answer: '[echo] hello' });
    expect(outcome.model).toBe('echo:default');
    expect(outcome.usage.totalTokens).toBeGreaterThan(0);
    expect(outcome.latencyMs).toBeGreaterThanOrEqual(0);
  });

  it('rejects invalid input with a ValidationError', async () => {
    await expect(
      executeCapability(faqCapability(), { question: '' }, {}, testDeps()),
    ).rejects.toBeInstanceOf(ValidationError);
  });

  it('rejects a model that is not on the governance allow-list', async () => {
    const capability = faqCapability({
      governance: {
        owner: 'x',
        dataClassification: 'internal',
        pii: false,
        modelAllowList: ['anthropic:claude-sonnet-5'],
      },
    });
    await expect(
      executeCapability(capability, { question: 'hi' }, {}, testDeps()),
    ).rejects.toBeInstanceOf(ForbiddenError);
  });

  it('raises InternalError when output violates the schema', async () => {
    const capability = faqCapability({
      // parseOutput returns a non-string answer, violating FAQ_OUTPUT.
      parseOutput: () => ({ answer: 123 }) as never,
    });
    await expect(
      executeCapability(capability, { question: 'hi' }, {}, testDeps()),
    ).rejects.toBeInstanceOf(InternalError);
  });

  it('raises InternalError when parseOutput throws', async () => {
    const capability = faqCapability({
      parseOutput: () => {
        throw new Error('boom');
      },
    });
    await expect(
      executeCapability(capability, { question: 'hi' }, {}, testDeps()),
    ).rejects.toBeInstanceOf(InternalError);
  });

  it('produces schema-valid output', async () => {
    const outcome = await executeCapability(
      faqCapability(),
      { question: 'hi' },
      {},
      testDeps(),
    );
    expect(FAQ_OUTPUT.safeParse(outcome.output).success).toBe(true);
  });
});
