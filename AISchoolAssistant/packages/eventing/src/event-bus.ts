import type { DomainEvent } from './event';

/** A handler invoked for each matching event. Must not throw silently-critical. */
export type EventHandler = (event: DomainEvent) => void | Promise<void>;

/** Handle returned by `subscribe`; call `unsubscribe` to stop receiving. */
export interface Subscription {
  unsubscribe(): void;
}

/**
 * The transport port for domain events. Business code depends only on this
 * interface — never on a broker SDK — so the in-memory bus (dev/test) and a
 * NATS JetStream adapter (production) are interchangeable.
 *
 * `subscribe('*', ...)` receives every event.
 */
export interface EventBus {
  publish(event: DomainEvent): Promise<void>;
  subscribe(type: string, handler: EventHandler): Subscription;
}

/** Wildcard subscription key that receives all event types. */
export const ALL_EVENTS = '*';

/**
 * In-process event bus. Delivers synchronously-awaited, in registration order,
 * to type-specific and wildcard subscribers. A throwing handler does not
 * prevent delivery to the others; the first error is rethrown after all
 * handlers have run, so failures are visible without losing fan-out.
 */
export class InMemoryEventBus implements EventBus {
  private readonly handlers = new Map<string, Set<EventHandler>>();

  subscribe(type: string, handler: EventHandler): Subscription {
    const set = this.handlers.get(type) ?? new Set<EventHandler>();
    set.add(handler);
    this.handlers.set(type, set);
    return {
      unsubscribe: () => {
        this.handlers.get(type)?.delete(handler);
      },
    };
  }

  async publish(event: DomainEvent): Promise<void> {
    const targets = [
      ...(this.handlers.get(event.type) ?? []),
      ...(this.handlers.get(ALL_EVENTS) ?? []),
    ];

    let firstError: unknown;
    for (const handler of targets) {
      try {
        await handler(event);
      } catch (error) {
        firstError ??= error;
      }
    }
    if (firstError) {
      throw firstError;
    }
  }
}
