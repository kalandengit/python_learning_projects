import { ConflictError, NotFoundError } from '@asa/errors';
import {
  capabilityKey,
  type CapabilityDefinition,
  type CapabilityStatus,
  type RegisteredCapability,
} from './capability';
import type { EvaluationReport } from './evaluation';
import { evaluateCapability } from './evaluation-runner';
import type { ExecutionDeps } from './execution';

/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyCapability = RegisteredCapability<any, any>;

/**
 * The enterprise catalog of AI capabilities. Capabilities are registered as
 * `draft` and can only be promoted to `published` once their evaluation suite
 * passes threshold — encoding the constitution's rule that *every capability
 * requires evaluation* and an "evaluation-less" capability cannot ship.
 */
export class CapabilityRegistry {
  private readonly capabilities = new Map<string, AnyCapability>();

  /** Register a capability in `draft`. Duplicate id+version is rejected. */
  register<Input, Output>(
    definition: CapabilityDefinition<Input, Output>,
  ): void {
    const key = capabilityKey(definition.id, definition.version);
    if (this.capabilities.has(key)) {
      throw new ConflictError(`Capability "${key}" is already registered.`);
    }
    this.capabilities.set(key, { definition, status: 'draft' });
  }

  /**
   * Run the capability's evaluation and, when it passes, mark it `published`.
   * Returns the report either way; throws only when promotion is attempted but
   * the gate fails.
   */
  async publish(
    id: string,
    version: string,
    deps: ExecutionDeps,
  ): Promise<EvaluationReport> {
    const entry = this.require(id, version);
    const report = await evaluateCapability(entry.definition, deps);
    if (!report.ok) {
      throw new ConflictError(
        `Capability "${capabilityKey(id, version)}" cannot be published: ` +
          `pass rate ${report.passRate.toFixed(2)} < threshold ${report.threshold}.`,
      );
    }
    entry.status = 'published';
    return report;
  }

  /** Register then immediately evaluate + publish. */
  async registerAndPublish<Input, Output>(
    definition: CapabilityDefinition<Input, Output>,
    deps: ExecutionDeps,
  ): Promise<EvaluationReport> {
    this.register(definition);
    return this.publish(definition.id, definition.version, deps);
  }

  get(id: string, version: string): AnyCapability {
    return this.require(id, version);
  }

  status(id: string, version: string): CapabilityStatus {
    return this.require(id, version).status;
  }

  has(id: string, version: string): boolean {
    return this.capabilities.has(capabilityKey(id, version));
  }

  /** All registered capabilities (id, version, status), for discovery. */
  list(): Array<{ id: string; version: string; status: CapabilityStatus }> {
    return [...this.capabilities.values()].map((entry) => ({
      id: entry.definition.id,
      version: entry.definition.version,
      status: entry.status,
    }));
  }

  private require(id: string, version: string): AnyCapability {
    const entry = this.capabilities.get(capabilityKey(id, version));
    if (!entry) {
      throw new NotFoundError(
        `Capability "${capabilityKey(id, version)}" is not registered.`,
      );
    }
    return entry;
  }
}
