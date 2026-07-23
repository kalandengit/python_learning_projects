import type { AgentDefinition } from '@asa/agent-runtime';

/**
 * Reference agent wiring the multi-agent runtime end-to-end. It routes to the
 * deterministic `echo:default` model (runnable offline) and is permitted the
 * `add` tool. Swap the model for a real one and the loop performs genuine
 * tool-calling — the runtime is unchanged.
 */
export const assistantAgent: AgentDefinition = {
  id: 'assistant',
  version: '1.0.0',
  description: 'A helpful school assistant that can use tools.',
  instructions:
    'You are a helpful school assistant. Use the available tools when a ' +
    'calculation or lookup is needed, then answer concisely.',
  model: 'echo:default',
  tools: ['add'],
  maxSteps: 5,
  governance: {
    owner: 'platform-ai',
    dataClassification: 'internal',
    pii: false,
    modelAllowList: ['echo:default'],
    tags: ['assistant', 'reference'],
  },
};
