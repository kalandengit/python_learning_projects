# ADR-0006: Event-Driven Architecture + Event Catalog

- **Status:** Accepted
- **Date:** 2026-07-23
- **Context:** Master Spec #6 (Event Catalog), Codex event-driven principle;
  WP-4.

## Decision

Cross-context communication is **event-driven**, and every event is governed by
an **Event Catalog** (`@asa/eventing`).

1. **Envelope** — all events share a standardized `DomainEvent` envelope
   (CloudEvents-inspired): `id`, `type`, `version`, `occurredAt`, `tenantId`,
   `correlationId`, `actor`, `subject`, `data`.
2. **Event Catalog** — the authoritative registry of event types (name +
   version + zod schema). Only cataloged events may be published, and payloads
   are validated against the registered schema — the contract for what may flow
   on the bus (analogous to the Capability Registry for AI).
3. **Bus port** — business code depends on an `EventBus` interface, never a
   broker SDK. `InMemoryEventBus` serves dev/test; a NATS JetStream adapter is
   the production implementation (deferred, drop-in).
4. **Publisher** — `EventPublisher` is the single emission path: it fills the
   envelope, validates against the catalog, publishes, and records the emission
   for observability. Business code never puts a raw event on the bus.
5. **Projections (CQRS)** — read models (e.g. the Learner Digital Twin,
   ADR-0007) subscribe to events and fold them into a projection; they are
   never written directly.

## Motivation

- Decouples bounded contexts (SIS, LMS, AI) — producers and consumers evolve
  independently.
- The catalog + schema validation prevents malformed or undocumented events,
  and versions the contract.
- The envelope carries tenant + correlation ids, so events are tenant-isolated
  and traceable end-to-end.

## Rules (enforced)

- Publishing an uncataloged event type, or a payload that fails its schema, is
  rejected — nothing reaches the bus.
- Every event carries `tenantId` and `correlationId` where available.
- Read models are derived from events only (no direct writes to projections).

## Alternatives considered

- **Direct service-to-service calls** — rejected: tight coupling, cascading
  failures, no audit trail.
- **Un-cataloged pub/sub** — rejected: no contract, no validation, schema drift.

## Consequences

- `@asa/eventing` ships the envelope, catalog, bus port + in-memory bus,
  publisher, and NestJS `EventingModule`. The service template registers learner
  events and drives the Digital Twin projection from them.
- The NATS JetStream adapter, dead-letter handling, and at-least-once delivery
  semantics land with the production broker in a later WP.
- AI capability/agent invocations (ADR-0002/0005) emit standardized events into
  this catalog for unified AI Observability.
