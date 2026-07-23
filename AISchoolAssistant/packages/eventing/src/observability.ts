/** Record emitted for every published event (for tracing/audit). */
export interface EventPublishRecord {
  id: string;
  type: string;
  version: string;
  tenantId?: string;
  subject?: string;
  correlationId?: string;
  actor?: string;
  timestamp: string;
}

/** Sink that receives publish records. Implementations must not throw. */
export interface EventObservabilitySink {
  record(record: EventPublishRecord): void | Promise<void>;
}

/** Retains records in memory — useful for tests and local inspection. */
export class InMemoryEventSink implements EventObservabilitySink {
  readonly records: EventPublishRecord[] = [];

  record(record: EventPublishRecord): void {
    this.records.push(record);
  }
}

/** Forwards records to a log function (defaults to structured console output). */
export class LoggingEventSink implements EventObservabilitySink {
  constructor(
    private readonly log: (record: EventPublishRecord) => void = (record) =>
      // eslint-disable-next-line no-console
      console.info(JSON.stringify({ msg: 'event.published', ...record })),
  ) {}

  record(record: EventPublishRecord): void {
    this.log(record);
  }
}
