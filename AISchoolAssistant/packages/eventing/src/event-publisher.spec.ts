import { z } from 'zod';
import { ValidationError } from '@asa/errors';
import { EventCatalog } from './event-catalog';
import { InMemoryEventBus } from './event-bus';
import { EventPublisher } from './event-publisher';
import { InMemoryEventSink } from './observability';
import type { DomainEvent } from './event';

function setup() {
  const catalog = new EventCatalog([
    {
      type: 'learner.lesson.completed',
      version: '2',
      schema: z.object({ learnerId: z.string(), lessonId: z.string() }),
    },
  ]);
  const bus = new InMemoryEventBus();
  const sink = new InMemoryEventSink();
  const publisher = new EventPublisher({ catalog, bus, sink });
  return { catalog, bus, sink, publisher };
}

describe('EventPublisher', () => {
  it('fills the envelope, validates, and delivers to subscribers', async () => {
    const { bus, publisher } = setup();
    const received: DomainEvent[] = [];
    bus.subscribe('learner.lesson.completed', (e) => {
      received.push(e);
    });

    const event = await publisher.publish({
      type: 'learner.lesson.completed',
      data: { learnerId: 'l1', lessonId: 'x' },
      subject: 'l1',
      tenantId: 't1',
      correlationId: 'c1',
      actor: 'teacher-1',
    });

    expect(event.id).toBeDefined();
    expect(event.version).toBe('2');
    expect(event.occurredAt).toBeDefined();
    expect(received).toHaveLength(1);
    expect(received[0].subject).toBe('l1');
    expect(received[0].tenantId).toBe('t1');
  });

  it('records the emission for observability', async () => {
    const { sink, publisher } = setup();
    await publisher.publish({
      type: 'learner.lesson.completed',
      data: { learnerId: 'l1', lessonId: 'x' },
    });
    expect(sink.records).toHaveLength(1);
    expect(sink.records[0].type).toBe('learner.lesson.completed');
  });

  it('rejects an invalid payload and publishes nothing', async () => {
    const { bus, publisher } = setup();
    let delivered = false;
    bus.subscribe('learner.lesson.completed', () => {
      delivered = true;
    });
    await expect(
      publisher.publish({
        type: 'learner.lesson.completed',
        data: { learnerId: 'l1' },
      }),
    ).rejects.toBeInstanceOf(ValidationError);
    expect(delivered).toBe(false);
  });
});
