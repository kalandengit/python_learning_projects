import { DynamicModule, Module, Provider } from '@nestjs/common';
import type { EventDefinition } from '../event-catalog';
import { EventCatalog } from '../event-catalog';
import { EventBus, InMemoryEventBus } from '../event-bus';
import { EventPublisher } from '../event-publisher';
import {
  LoggingEventSink,
  type EventObservabilitySink,
} from '../observability';
import { EVENT_BUS, EVENT_CATALOG, EVENT_OBSERVABILITY } from './tokens';

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Options for {@link EventingModule.forRoot}. */
export interface EventingModuleOptions {
  /** Event types to register in the catalog. */
  events?: EventDefinition<any>[];
  /** Transport (defaults to the in-process {@link InMemoryEventBus}). */
  bus?: EventBus;
  /** Observability sink (defaults to a logging sink). */
  sink?: EventObservabilitySink;
}

/**
 * The event-driven core as a global NestJS module: the Event Catalog, the event
 * bus, and the catalog-validated {@link EventPublisher}. Features inject the
 * publisher to emit events and the bus to subscribe projections/handlers.
 */
@Module({})
export class EventingModule {
  static forRoot(options: EventingModuleOptions = {}): DynamicModule {
    const providers: Provider[] = [
      {
        provide: EVENT_CATALOG,
        useFactory: () => new EventCatalog(options.events ?? []),
      },
      {
        provide: EVENT_BUS,
        useFactory: () => options.bus ?? new InMemoryEventBus(),
      },
      {
        provide: EVENT_OBSERVABILITY,
        useFactory: () => options.sink ?? new LoggingEventSink(),
      },
      {
        provide: EventPublisher,
        useFactory: (
          catalog: EventCatalog,
          bus: EventBus,
          sink: EventObservabilitySink,
        ) => new EventPublisher({ catalog, bus, sink }),
        inject: [EVENT_CATALOG, EVENT_BUS, EVENT_OBSERVABILITY],
      },
    ];

    return {
      module: EventingModule,
      global: true,
      providers,
      exports: [EventPublisher, EVENT_CATALOG, EVENT_BUS, EVENT_OBSERVABILITY],
    };
  }
}
