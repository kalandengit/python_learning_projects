import { z } from 'zod';
import { ConflictError, NotFoundError, ValidationError } from '@asa/errors';
import { EventCatalog } from './event-catalog';

const lessonCompleted = {
  type: 'learner.lesson.completed',
  version: '1',
  schema: z.object({ learnerId: z.string(), lessonId: z.string() }),
};

describe('EventCatalog', () => {
  it('registers and looks up event definitions', () => {
    const catalog = new EventCatalog([lessonCompleted]);
    expect(catalog.has('learner.lesson.completed')).toBe(true);
    expect(catalog.list()).toEqual([
      { type: 'learner.lesson.completed', version: '1' },
    ]);
  });

  it('rejects duplicate registration', () => {
    const catalog = new EventCatalog([lessonCompleted]);
    expect(() => catalog.register(lessonCompleted)).toThrow(ConflictError);
  });

  it('throws NotFoundError for unknown types', () => {
    expect(() => new EventCatalog().get('nope')).toThrow(NotFoundError);
  });

  it('validates a correct payload and returns the version', () => {
    const catalog = new EventCatalog([lessonCompleted]);
    const result = catalog.validate('learner.lesson.completed', {
      learnerId: 'l1',
      lessonId: 'x',
    });
    expect(result.version).toBe('1');
  });

  it('rejects an invalid payload', () => {
    const catalog = new EventCatalog([lessonCompleted]);
    expect(() =>
      catalog.validate('learner.lesson.completed', { learnerId: 1 }),
    ).toThrow(ValidationError);
  });

  it('rejects publishing an uncataloged type', () => {
    expect(() => new EventCatalog().validate('ghost', {})).toThrow(
      NotFoundError,
    );
  });
});
