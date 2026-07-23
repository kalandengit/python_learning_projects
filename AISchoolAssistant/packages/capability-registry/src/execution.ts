import {
  AiProviderRegistry,
  ModelRouter,
  type ChatRequest,
  type TokenUsage,
} from '@asa/ai-sdk';
import { ForbiddenError, InternalError, ValidationError } from '@asa/errors';
import type { CapabilityContext, CapabilityDefinition } from './capability';

/** Collaborators the execution engine needs. */
export interface ExecutionDeps {
  providers: AiProviderRegistry;
  router: ModelRouter;
}

/** Telemetry captured alongside a capability's typed output. */
export interface ExecutionOutcome<Output> {
  output: Output;
  /** Concrete `provider:model` that produced the output. */
  model: string;
  usage: TokenUsage;
  latencyMs: number;
}

/**
 * The single, governed path from a capability + input to a typed output:
 *
 *   validate input → route model → enforce governance allow-list →
 *   build prompt → call the provider (via the AI SDK) → parse → validate output
 *
 * This is the *only* place a model is invoked, so "never bypass the registry /
 * always via the AI SDK" holds by construction. It performs no lifecycle
 * (published) or observability concerns — those belong to the executor — so it
 * can be reused as-is by the evaluation runner.
 */
export async function executeCapability<Input, Output>(
  definition: CapabilityDefinition<Input, Output>,
  rawInput: unknown,
  context: CapabilityContext,
  deps: ExecutionDeps,
): Promise<ExecutionOutcome<Output>> {
  const parsedInput = definition.inputSchema.safeParse(rawInput);
  if (!parsedInput.success) {
    throw new ValidationError(
      `Invalid input for capability "${definition.id}".`,
      parsedInput.error.issues.map((issue) => ({
        field: issue.path.join('.') || '(root)',
        message: issue.message,
      })),
    );
  }
  const input = parsedInput.data;

  const resolved = deps.router.resolve(definition.model);
  if (!definition.governance.modelAllowList.includes(resolved.ref)) {
    throw new ForbiddenError(
      `Model "${resolved.ref}" is not on the allow-list for capability "${definition.id}".`,
    );
  }

  const provider = deps.providers.get(resolved.providerId);
  const request: ChatRequest = {
    model: resolved.ref,
    messages: definition.buildPrompt(input, context),
    temperature: definition.temperature,
    maxTokens: definition.maxTokens,
    responseFormat: definition.responseFormat,
  };

  const startedAt = Date.now();
  const result = await provider.generate(request);
  const latencyMs = Date.now() - startedAt;

  let output: Output;
  try {
    output = definition.parseOutput(result, input);
  } catch (error) {
    throw new InternalError(
      `Capability "${definition.id}" failed to parse model output: ${
        error instanceof Error ? error.message : 'unknown error'
      }`,
    );
  }

  const parsedOutput = definition.outputSchema.safeParse(output);
  if (!parsedOutput.success) {
    throw new InternalError(
      `Capability "${definition.id}" produced output that failed its schema.`,
    );
  }

  return {
    output: parsedOutput.data,
    model: resolved.ref,
    usage: result.usage,
    latencyMs,
  };
}
