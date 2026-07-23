import {
  AiProviderRegistry,
  ModelRouter,
  type ChatMessage,
  type TokenUsage,
} from '@asa/ai-sdk';
import { ForbiddenError, ValidationError, isAppError } from '@asa/errors';
import type { AgentDefinition } from './agent';
import { AgentRegistry } from './agent';
import type { AgentContext } from './context';
import type { AgentObservabilitySink } from './observability';
import { ToolRegistry } from './tool';

/** Collaborators the agent executor depends on. */
export interface AgentExecutorDeps {
  agents: AgentRegistry;
  tools: ToolRegistry;
  providers: AiProviderRegistry;
  router: ModelRouter;
  sink: AgentObservabilitySink;
}

/** The input to an agent run. */
export interface AgentRunInput {
  goal: string;
}

/** The result of an agent run. */
export interface AgentRunResult {
  output: string;
  steps: number;
  toolsUsed: string[];
  finishReason: 'completed' | 'max_steps';
  model: string;
  usage: TokenUsage;
}

function addUsage(a: TokenUsage, b: TokenUsage): TokenUsage {
  return {
    promptTokens: a.promptTokens + b.promptTokens,
    completionTokens: a.completionTokens + b.completionTokens,
    totalTokens: a.totalTokens + b.totalTokens,
  };
}

/**
 * The multi-agent runtime's execution engine. Runs an agent's bounded
 * reasoning loop: prompt the model with the available tools, execute any tool
 * calls it makes (validating model-produced arguments and enforcing the
 * agent's tool allow-list), feed results back, and repeat until the model
 * answers or `maxSteps` is reached. Emits one observability event per run.
 */
export class AgentExecutor {
  constructor(private readonly deps: AgentExecutorDeps) {}

  async run(
    id: string,
    version: string,
    input: AgentRunInput,
    context: AgentContext = {},
  ): Promise<AgentRunResult> {
    const agent = this.deps.agents.get(id, version);
    const resolved = this.deps.router.resolve(agent.model);

    if (!agent.governance.modelAllowList.includes(resolved.ref)) {
      throw new ForbiddenError(
        `Model "${resolved.ref}" is not on the allow-list for agent "${id}".`,
      );
    }

    const provider = this.deps.providers.get(resolved.providerId);
    const toolDefs = this.deps.tools.toDefinitions(agent.tools);
    const messages: ChatMessage[] = [
      { role: 'system', content: agent.instructions },
      { role: 'user', content: input.goal },
    ];

    const toolsUsed: string[] = [];
    let usage: TokenUsage = {
      promptTokens: 0,
      completionTokens: 0,
      totalTokens: 0,
    };
    let lastText = '';
    const startedAt = Date.now();

    try {
      for (let step = 1; step <= agent.maxSteps; step += 1) {
        const result = await provider.generate({
          model: resolved.ref,
          messages,
          tools: toolDefs.length > 0 ? toolDefs : undefined,
          temperature: agent.temperature,
        });
        usage = addUsage(usage, result.usage);
        lastText = result.text;

        if (!result.toolCalls || result.toolCalls.length === 0) {
          return this.finish(
            id,
            version,
            resolved.ref,
            {
              output: result.text,
              steps: step,
              toolsUsed,
              finishReason: 'completed',
              model: resolved.ref,
              usage,
            },
            context,
            startedAt,
          );
        }

        messages.push({
          role: 'assistant',
          content: result.text,
          toolCalls: result.toolCalls,
        });

        for (const call of result.toolCalls) {
          const output = await this.runTool(agent, call, context);
          toolsUsed.push(call.name);
          messages.push({
            role: 'tool',
            name: call.name,
            toolCallId: call.id,
            content: JSON.stringify(output),
          });
        }
      }

      return this.finish(
        id,
        version,
        resolved.ref,
        {
          output: lastText,
          steps: agent.maxSteps,
          toolsUsed,
          finishReason: 'max_steps',
          model: resolved.ref,
          usage,
        },
        context,
        startedAt,
      );
    } catch (error) {
      await this.deps.sink.record({
        agentId: id,
        version,
        model: resolved.ref,
        success: false,
        steps: toolsUsed.length,
        toolsUsed,
        latencyMs: Date.now() - startedAt,
        tenantId: context.tenantId,
        actor: context.actor,
        correlationId: context.correlationId,
        errorCode: isAppError(error) ? error.code : 'internal_error',
        timestamp: new Date().toISOString(),
      });
      throw error;
    }
  }

  private async runTool(
    agent: AgentDefinition,
    call: { id: string; name: string; arguments: string },
    context: AgentContext,
  ): Promise<unknown> {
    if (!agent.tools.includes(call.name)) {
      throw new ForbiddenError(
        `Agent "${agent.id}" attempted to call unavailable tool "${call.name}".`,
      );
    }
    const tool = this.deps.tools.get(call.name);

    let rawArgs: unknown;
    try {
      rawArgs = call.arguments ? JSON.parse(call.arguments) : {};
    } catch {
      throw new ValidationError(
        `Tool "${call.name}" received malformed JSON arguments.`,
      );
    }

    const parsed = tool.inputSchema.safeParse(rawArgs);
    if (!parsed.success) {
      throw new ValidationError(
        `Tool "${call.name}" received invalid arguments.`,
        parsed.error.issues.map((issue) => ({
          field: issue.path.join('.') || '(root)',
          message: issue.message,
        })),
      );
    }

    return tool.execute(parsed.data, context);
  }

  private async finish(
    id: string,
    version: string,
    model: string,
    result: AgentRunResult,
    context: AgentContext,
    startedAt: number,
  ): Promise<AgentRunResult> {
    await this.deps.sink.record({
      agentId: id,
      version,
      model,
      success: true,
      steps: result.steps,
      toolsUsed: result.toolsUsed,
      latencyMs: Date.now() - startedAt,
      usage: result.usage,
      finishReason: result.finishReason,
      tenantId: context.tenantId,
      actor: context.actor,
      correlationId: context.correlationId,
      timestamp: new Date().toISOString(),
    });
    return result;
  }
}
