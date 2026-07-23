/**
 * The standardized domain-event envelope (CloudEvents-inspired). Every event on
 * the bus carries the same metadata so consumers, tracing, and audit are
 * uniform. `data` is the type-specific payload validated by the Event Catalog.
 */
export interface DomainEvent<T = unknown> {
  /** Unique event id (idempotency key). */
  id: string;
  /** Event name, e.g. `learner.lesson.completed`. */
  type: string;
  /** Schema version of `data`, e.g. `1`. */
  version: string;
  /** ISO-8601 time the event occurred. */
  occurredAt: string;
  /** Tenant the event belongs to (multi-tenant isolation). */
  tenantId?: string;
  /** Correlation id linking this event to a request/trace. */
  correlationId?: string;
  /** Principal subject that caused the event. */
  actor?: string;
  /** The entity the event is about (e.g. a learner id). */
  subject?: string;
  /** Type-specific payload. */
  data: T;
}

/** Fields a caller supplies; the publisher fills in id/occurredAt/version. */
export interface EventInput<T> {
  type: string;
  data: T;
  subject?: string;
  tenantId?: string;
  correlationId?: string;
  actor?: string;
}
