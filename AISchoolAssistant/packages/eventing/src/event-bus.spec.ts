import { ALL_EVENTS, InMemoryEventBus } from './event-bus';
import type { DomainEvent } from './event';

function event(type: string): DomainEvent {
  return {
    id: 'e1',
    type,
    version: '1',
    occurredAt: new Date().toISOString(),
    data: {},
  };
}

describe('InMemoryEventBus', () => {
  it('delivers to type-specific subscribers', async () => {
    const bus = new InMemoryEventBus();
    const seen: string[] = [];
    bus.subscribe('a', () => {
      seen.push('a-handler');
    });
    bus.subscribe('b', () => {
      seen.push('b-handler');
    });
    await bus.publish(event('a'));
    expect(seen).toEqual(['a-handler']);
  });

  it('delivers to wildcard subscribers for every type', async () => {
    const bus = new InMemoryEventBus();
    const types: string[] = [];
    bus.subscribe(ALL_EVENTS, (e) => {
      types.push(e.type);
    });
    await bus.publish(event('a'));
    await bus.publish(event('b'));
    expect(types).toEqual(['a', 'b']);
  });

  it('stops delivering after unsubscribe', async () => {
    const bus = new InMemoryEventBus();
    let count = 0;
    const sub = bus.subscribe('a', () => {
      count += 1;
    });
    await bus.publish(event('a'));
    sub.unsubscribe();
    await bus.publish(event('a'));
    expect(count).toBe(1);
  });

  it('runs all handlers even if one throws, then rethrows', async () => {
    const bus = new InMemoryEventBus();
    let reached = false;
    bus.subscribe('a', () => {
      throw new Error('boom');
    });
    bus.subscribe('a', () => {
      reached = true;
    });
    await expect(bus.publish(event('a'))).rejects.toThrow('boom');
    expect(reached).toBe(true);
  });

  it('awaits async handlers', async () => {
    const bus = new InMemoryEventBus();
    let done = false;
    bus.subscribe('a', async () => {
      await new Promise((r) => setTimeout(r, 5));
      done = true;
    });
    await bus.publish(event('a'));
    expect(done).toBe(true);
  });
});
