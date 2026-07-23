import { z } from 'zod';
import type { AgentTool } from '@asa/agent-runtime';

/**
 * A trivial deterministic tool the reference agent may call. Real tools wrap
 * domain services or MCP endpoints; the pattern (JSON-Schema `parameters` for
 * the model + a zod `inputSchema` guarding execution) is the same.
 */
export const addTool: AgentTool<{ a: number; b: number }, number> = {
  name: 'add',
  description: 'Adds two numbers and returns the sum.',
  parameters: {
    type: 'object',
    properties: { a: { type: 'number' }, b: { type: 'number' } },
    required: ['a', 'b'],
  },
  inputSchema: z.object({ a: z.number(), b: z.number() }),
  execute: ({ a, b }) => a + b,
};
