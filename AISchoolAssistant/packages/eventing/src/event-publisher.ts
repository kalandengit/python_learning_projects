import { randomUUID } from 'node:crypto';
import type { DomainEvent, EventInput } from './event';
import type { EventBus } from './event-bus';
import type { EventCatalog } from './event-catalog';
import type { EventObservabilitySink } from './observability';

/** Collaborators the publisher depends on. */
export interface EventPublisherDeps {
  catalog: EventCatalog;
  bus: EventBus;
  sink: EventObservabilitySink;
}

/**
 * The single, catalog-validated path for emitting domain events: it fills the
 * envelope (id, timestamp, schema version), validates the payload against the
 * Event Catalog, publishes to the bus, and records the emission for
 * observability. Business code never constructs a raw event onto the bus.
 */
export class EventPublisher {
  constructor(private readonly deps: EventPublisherDeps) {}

  async publish<T>(input: EventInput<T>): Promise<DomainEvent<T>> {
    const { data, version } = this.deps.catalog.validate(
      input.type,
      input.data,
    );

    const event: DomainEvent<T> = {
      id: randomUUID(),
      type: input.type,
      version,
      occurredAt: new Date().toISOString(),
      tenantId: input.tenantId,
      correlationId: input.correlationId,
      actor: input.actor,
      subject: input.subject,
      data: data as T,
    };

    await this.deps.bus.publish(event);

    await this.deps.sink.record({
      id: event.id,
      type: event.type,
      version: event.version,
      tenantId: event.tenantId,
      subject: event.subject,
      correlationId: event.correlationId,
      actor: event.actor,
      timestamp: event.occurredAt,
    });

    return event;
  }
}
