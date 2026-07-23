import { AiProviderRegistry, ModelRouter } from '@asa/ai-sdk';
import { ConflictError, isAppError } from '@asa/errors';
import type { CapabilityContext } from './capability';
import type { CapabilityRegistry } from './capability-registry';
import { executeCapability, type ExecutionOutcome } from './execution';
import type { AiObservabilitySink } from './observability';

/** Collaborators the executor depends on. */
export interface CapabilityExecutorDeps {
  registry: CapabilityRegistry;
  providers: AiProviderRegistry;
  router: ModelRouter;
  sink: AiObservabilitySink;
}

/**
 * The single entry point features use to run AI: `invoke(id, version, input)`.
 * It enforces that only **published** capabilities run, executes them through
 * the governed path, and emits an observability event for every attempt
 * (success or failure) — so no invocation escapes governance or telemetry.
 */
export class CapabilityExecutor {
  constructor(private readonly deps: CapabilityExecutorDeps) {}

  async invoke<Output = unknown>(
    id: string,
    version: string,
    input: unknown,
    context: CapabilityContext = {},
  ): Promise<ExecutionOutcome<Output>> {
    const entry = this.deps.registry.get(id, version);
    if (entry.status !== 'published') {
      throw new ConflictError(
        `Capability "${id}@${version}" is not published and cannot be invoked.`,
      );
    }

    try {
      const outcome = (await executeCapability(
        entry.definition,
        input,
        context,
        { providers: this.deps.providers, router: this.deps.router },
      )) as ExecutionOutcome<Output>;

      await this.deps.sink.record({
        capabilityId: id,
        version,
        model: outcome.model,
        success: true,
        latencyMs: outcome.latencyMs,
        usage: outcome.usage,
        tenantId: context.tenantId,
        actor: context.actor,
        correlationId: context.correlationId,
        timestamp: new Date().toISOString(),
      });

      return outcome;
    } catch (error) {
      await this.deps.sink.record({
        capabilityId: id,
        version,
        success: false,
        latencyMs: 0,
        tenantId: context.tenantId,
        actor: context.actor,
        correlationId: context.correlationId,
        errorCode: isAppError(error) ? error.code : 'internal_error',
        timestamp: new Date().toISOString(),
      });
      throw error;
    }
  }
}
