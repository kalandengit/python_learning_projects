import { z } from 'zod';
import {
  AiProviderRegistry,
  ModelRouter,
  type LanguageModelProvider,
} from '@asa/ai-sdk';
import type { AgentDefinition } from '../agent';
import { AgentRegistry } from '../agent';
import type { AgentTool } from '../tool';
import { ToolRegistry } from '../tool';
import { InMemoryAgentSink } from '../observability';
import { AgentExecutor } from '../agent-executor';

/** A deterministic calculator tool used to exercise the tool-calling loop. */
export const calculatorTool: AgentTool<{ a: number; b: number }, number> = {
  name: 'add',
  description: 'Adds two numbers.',
  parameters: {
    type: 'object',
    properties: { a: { type: 'number' }, b: { type: 'number' } },
    required: ['a', 'b'],
  },
  inputSchema: z.object({ a: z.number(), b: z.number() }),
  execute: ({ a, b }) => a + b,
};

/** A reference agent allowed to use the `add` tool on the echo/scripted model. */
export function assistantAgent(
  overrides: Partial<AgentDefinition> = {},
): AgentDefinition {
  return {
    id: 'assistant',
    version: '1.0.0',
    description: 'A helpful assistant that can add numbers.',
    instructions: 'Use tools when a calculation is needed.',
    model: 'scripted:default',
    tools: ['add'],
    maxSteps: 4,
    governance: {
      owner: 'platform-ai',
      dataClassification: 'internal',
      pii: false,
      modelAllowList: ['scripted:default'],
    },
    ...overrides,
  };
}

/** Build an executor around the given provider, with the fixtures registered. */
export function makeExecutor(
  provider: LanguageModelProvider,
  agentOverrides: Partial<AgentDefinition> = {},
): {
  executor: AgentExecutor;
  sink: InMemoryAgentSink;
  agents: AgentRegistry;
} {
  const model = `${provider.id}:default`;
  const agents = new AgentRegistry([
    assistantAgent({
      model,
      governance: {
        owner: 'platform-ai',
        dataClassification: 'internal',
        pii: false,
        modelAllowList: [model],
      },
      ...agentOverrides,
    }),
  ]);
  const tools = new ToolRegistry([calculatorTool]);
  const providers = new AiProviderRegistry([provider]);
  const router = new ModelRouter({}, model);
  const sink = new InMemoryAgentSink();
  const executor = new AgentExecutor({
    agents,
    tools,
    providers,
    router,
    sink,
  });
  return { executor, sink, agents };
}
