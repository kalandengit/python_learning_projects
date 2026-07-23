import type { TokenUsage } from '@asa/ai-sdk';

/**
 * A standardized event emitted for every capability invocation (success or
 * failure). This is the AI-Observability record — later forwarded to the Event
 * Catalog / tracing backend. It carries governance-relevant context (tenant,
 * actor) plus cost/latency signals.
 */
export interface CapabilityInvocationEvent {
  capabilityId: string;
  version: string;
  /** Concrete `provider:model` used, when resolution succeeded. */
  model?: string;
  success: boolean;
  latencyMs: number;
  usage?: TokenUsage;
  tenantId?: string;
  actor?: string;
  correlationId?: string;
  /** Machine error code when `success` is false. */
  errorCode?: string;
  /** ISO-8601 timestamp. */
  timestamp: string;
}

/** Sink that receives invocation events. Implementations must not throw. */
export interface AiObservabilitySink {
  record(event: CapabilityInvocationEvent): void | Promise<void>;
}

/** Retains events in memory — useful for tests and local inspection. */
export class InMemoryObservabilitySink implements AiObservabilitySink {
  readonly events: CapabilityInvocationEvent[] = [];

  record(event: CapabilityInvocationEvent): void {
    this.events.push(event);
  }
}

/** Forwards events to a log function (defaults to structured console output). */
export class LoggingObservabilitySink implements AiObservabilitySink {
  constructor(
    private readonly log: (event: CapabilityInvocationEvent) => void = (
      event,
    ) =>
      // eslint-disable-next-line no-console
      console.info(JSON.stringify({ msg: 'ai.capability.invoked', ...event })),
  ) {}

  record(event: CapabilityInvocationEvent): void {
    this.log(event);
  }
}
