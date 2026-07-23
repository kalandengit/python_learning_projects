import { z } from 'zod';
import { AiProviderRegistry, EchoProvider, ModelRouter } from '@asa/ai-sdk';
import type { CapabilityDefinition } from '../capability';
import type { ExecutionDeps } from '../execution';

export const FAQ_INPUT = z.object({ question: z.string().min(1) });
export const FAQ_OUTPUT = z.object({ answer: z.string().min(1) });

export type FaqInput = z.infer<typeof FAQ_INPUT>;
export type FaqOutput = z.infer<typeof FAQ_OUTPUT>;

/**
 * A deterministic reference capability used across tests. Backed by the
 * EchoProvider, so its output (`[echo] <question>`) is fully predictable and
 * its evaluation is reproducible.
 */
export function faqCapability(
  overrides: Partial<CapabilityDefinition<FaqInput, FaqOutput>> = {},
): CapabilityDefinition<FaqInput, FaqOutput> {
  return {
    id: 'faq-answer',
    version: '1.0.0',
    description: 'Answers a frequently-asked question.',
    model: 'echo:default',
    inputSchema: FAQ_INPUT,
    outputSchema: FAQ_OUTPUT,
    buildPrompt: (input) => [
      { role: 'system', content: 'Answer concisely.' },
      { role: 'user', content: input.question },
    ],
    parseOutput: (result) => ({ answer: result.text }),
    governance: {
      owner: 'platform-ai',
      dataClassification: 'internal',
      pii: false,
      modelAllowList: ['echo:default'],
    },
    evaluation: {
      minPassRate: 1,
      cases: [
        {
          name: 'echoes the question',
          input: { question: 'What time is class?' },
          assert: (output) => output.answer.includes('What time is class?'),
        },
        {
          name: 'is prefixed by the echo marker',
          input: { question: 'hello' },
          assert: (output) => output.answer.startsWith('[echo]'),
        },
      ],
    },
    ...overrides,
  };
}

/** Standard execution deps: an EchoProvider registry + a default-aliased router. */
export function testDeps(): ExecutionDeps {
  return {
    providers: new AiProviderRegistry([new EchoProvider()]),
    router: new ModelRouter({}, 'echo:default'),
  };
}
