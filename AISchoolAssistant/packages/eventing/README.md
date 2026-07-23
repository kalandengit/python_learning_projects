# @asa/eventing

Event-driven core for the AI School Assistant platform (ADR-0006): a
standardized event envelope, an **Event Catalog**, a transport-agnostic bus, and
a catalog-validated publisher.

## Concepts

- **`DomainEvent`** — the standardized envelope: `id`, `type`, `version`,
  `occurredAt`, `tenantId`, `correlationId`, `actor`, `subject`, `data`.
- **`EventCatalog`** — the registry of event types (name + version + zod
  schema). Only cataloged events may be published; payloads are validated.
- **`EventBus`** — the transport port. `InMemoryEventBus` (dev/test) delivers to
  type-specific and `*` wildcard subscribers; a NATS JetStream adapter is the
  production drop-in.
- **`EventPublisher`** — the single emission path: fills the envelope, validates
  against the catalog, publishes, and records the emission for observability.

## Guarantees (enforced)

- Publishing an **uncataloged** type or an **invalid payload** is rejected —
  nothing reaches the bus.
- Read models are **projections**: subscribe to events and fold them into state;
  never write the read model directly.

## NestJS usage

```ts
EventingModule.forRoot({ events: [lessonCompleted, assessmentScored] });

// publish
await publisher.publish({
  type: 'learner.lesson.completed',
  data,
  subject,
  tenantId,
});

// project
bus.subscribe('learner.lesson.completed', (e) => applyToTwin(e));
```

## Testing

Use `InMemoryEventBus` + `InMemoryEventSink`: publish through the catalog and
assert both delivery to subscribers and the recorded emission — fully
deterministic, no broker required.
