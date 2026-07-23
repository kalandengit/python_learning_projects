import type { ZodType } from 'zod';
import type { ChatMessage, ChatResult } from '@asa/ai-sdk';
import type { EvaluationSuite } from './evaluation';

/** Sensitivity of the data a capability processes (drives handling controls). */
export type DataClassification =
  'public' | 'internal' | 'confidential' | 'restricted';

/**
 * Governance metadata every capability must declare. Enforced at registration
 * and invocation: the routed model must be on the allow-list, and the metadata
 * is attached to observability events for audit.
 */
export interface GovernanceMetadata {
  /** Accountable owner (team or individual). */
  owner: string;
  /** Classification of the data the capability handles. */
  dataClassification: DataClassification;
  /** Whether inputs/outputs may contain personal data. */
  pii: boolean;
  /** Concrete `provider:model` references this capability is permitted to use. */
  modelAllowList: string[];
  /** Free-form labels for discovery and policy. */
  tags?: string[];
}

/** Lifecycle status. Only `published` capabilities may be invoked. */
export type CapabilityStatus = 'draft' | 'published';

/** Ambient context for an invocation (who/where), used for audit + tenancy. */
export interface CapabilityContext {
  tenantId?: string;
  /** Principal subject making the call. */
  actor?: string;
  correlationId?: string;
}

/**
 * A **capability**: the named, versioned unit of AI functionality. It fully
 * specifies its I/O contract (zod schemas), how a prompt is built, how the
 * model output is parsed, which model it routes to, its governance metadata,
 * and the evaluation suite that gates promotion to `published`.
 *
 * Features invoke a registered capability by id + version — never a raw model
 * call (ADR-0002).
 */
export interface CapabilityDefinition<Input, Output> {
  id: string;
  /** Semantic version, e.g. `1.0.0`. */
  version: string;
  description: string;
  /** Logical model reference or routing alias resolved by the ModelRouter. */
  model: string;
  inputSchema: ZodType<Input>;
  outputSchema: ZodType<Output>;
  buildPrompt: (input: Input, context: CapabilityContext) => ChatMessage[];
  parseOutput: (result: ChatResult, input: Input) => Output;
  governance: GovernanceMetadata;
  evaluation: EvaluationSuite<Input, Output>;
  temperature?: number;
  maxTokens?: number;
  responseFormat?: 'text' | 'json';
}

/** A registered capability plus its mutable lifecycle status. */
export interface RegisteredCapability<Input, Output> {
  definition: CapabilityDefinition<Input, Output>;
  status: CapabilityStatus;
}

/** Registry key for a capability id + version. */
export function capabilityKey(id: string, version: string): string {
  return `${id}@${version}`;
}
