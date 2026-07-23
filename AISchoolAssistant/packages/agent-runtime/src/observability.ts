import type { TokenUsage } from '@asa/ai-sdk';

/** Standardized event emitted for every agent run (success or failure). */
export interface AgentRunEvent {
  agentId: string;
  version: string;
  model?: string;
  success: boolean;
  steps: number;
  /** Names of tools invoked during the run, in order. */
  toolsUsed: string[];
  latencyMs: number;
  usage?: TokenUsage;
  finishReason?: 'completed' | 'max_steps';
  tenantId?: string;
  actor?: string;
  correlationId?: string;
  errorCode?: string;
  timestamp: string;
}

/** Sink that receives agent-run events. Implementations must not throw. */
export interface AgentObservabilitySink {
  record(event: AgentRunEvent): void | Promise<void>;
}

/** Retains events in memory — useful for tests and local inspection. */
export class InMemoryAgentSink implements AgentObservabilitySink {
  readonly events: AgentRunEvent[] = [];

  record(event: AgentRunEvent): void {
    this.events.push(event);
  }
}

/** Forwards events to a log function (defaults to structured console output). */
export class LoggingAgentSink implements AgentObservabilitySink {
  constructor(
    private readonly log: (event: AgentRunEvent) => void = (event) =>
      // eslint-disable-next-line no-console
      console.info(JSON.stringify({ msg: 'ai.agent.run', ...event })),
  ) {}

  record(event: AgentRunEvent): void {
    this.log(event);
  }
}
