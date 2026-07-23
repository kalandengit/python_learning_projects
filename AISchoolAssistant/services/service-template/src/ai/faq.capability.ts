import { z } from 'zod';
import type { CapabilityDefinition } from '@asa/capability-registry';

export const faqInputSchema = z.object({
  question: z.string().min(1).max(500),
});
export const faqOutputSchema = z.object({
  answer: z.string().min(1),
});

export type FaqInput = z.infer<typeof faqInputSchema>;
export type FaqOutput = z.infer<typeof faqOutputSchema>;

/**
 * Reference capability wiring the whole AI stack end-to-end. It routes to the
 * deterministic `echo:default` model so it is runnable offline and its
 * evaluation is reproducible — replace the model + prompt with a real one for a
 * production capability. Registered + evaluated + published at boot by the
 * `AiModule` (see `app.module.ts`).
 */
export const faqCapability: CapabilityDefinition<FaqInput, FaqOutput> = {
  id: 'faq-answer',
  version: '1.0.0',
  description: 'Answers a school FAQ question.',
  model: 'echo:default',
  inputSchema: faqInputSchema,
  outputSchema: faqOutputSchema,
  buildPrompt: (input) => [
    {
      role: 'system',
      content: 'You are a helpful school assistant. Answer concisely.',
    },
    { role: 'user', content: input.question },
  ],
  parseOutput: (result) => ({ answer: result.text }),
  governance: {
    owner: 'platform-ai',
    dataClassification: 'internal',
    pii: false,
    modelAllowList: ['echo:default'],
    tags: ['faq', 'reference'],
  },
  evaluation: {
    minPassRate: 1,
    cases: [
      {
        name: 'answer reflects the question',
        input: { question: 'When does term start?' },
        assert: (output) => output.answer.includes('When does term start?'),
      },
      {
        name: 'answer is non-empty',
        input: { question: 'hello' },
        assert: (output) => output.answer.trim().length > 0,
      },
    ],
  },
};
