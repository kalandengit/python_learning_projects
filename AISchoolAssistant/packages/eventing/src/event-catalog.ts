import type { ZodType } from 'zod';
import { ConflictError, NotFoundError, ValidationError } from '@asa/errors';

/** A registered event type: its name, schema version, and payload schema. */
export interface EventDefinition<T = unknown> {
  type: string;
  version: string;
  /** zod schema validating the event `data` payload. */
  schema: ZodType<T>;
  description?: string;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyDefinition = EventDefinition<any>;

/**
 * The **Event Catalog**: the authoritative registry of event types. Only
 * cataloged events may be published, and their payloads are validated against
 * the registered schema — the enterprise contract for what may flow on the bus
 * (analogous to the Capability Registry for AI).
 */
export class EventCatalog {
  private readonly definitions = new Map<string, AnyDefinition>();

  constructor(definitions: AnyDefinition[] = []) {
    for (const definition of definitions) {
      this.register(definition);
    }
  }

  register<T>(definition: EventDefinition<T>): void {
    if (this.definitions.has(definition.type)) {
      throw new ConflictError(
        `Event type "${definition.type}" is already registered.`,
      );
    }
    this.definitions.set(definition.type, definition);
  }

  get(type: string): AnyDefinition {
    const definition = this.definitions.get(type);
    if (!definition) {
      throw new NotFoundError(`Event type "${type}" is not registered.`);
    }
    return definition;
  }

  has(type: string): boolean {
    return this.definitions.has(type);
  }

  list(): Array<{ type: string; version: string }> {
    return [...this.definitions.values()].map((d) => ({
      type: d.type,
      version: d.version,
    }));
  }

  /** Validate a payload against the cataloged schema; throws on mismatch. */
  validate(type: string, data: unknown): { data: unknown; version: string } {
    const definition = this.get(type);
    const result = definition.schema.safeParse(data);
    if (!result.success) {
      throw new ValidationError(
        `Invalid payload for event "${type}".`,
        result.error.issues.map((issue) => ({
          field: issue.path.join('.') || '(root)',
          message: issue.message,
        })),
      );
    }
    return { data: result.data, version: definition.version };
  }
}
