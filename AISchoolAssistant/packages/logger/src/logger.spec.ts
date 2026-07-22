import { describe, it, expect } from 'vitest';
import { createLogger } from './logger';

describe('createLogger', () => {
  it('creates a logger with the requested level and base fields', () => {
    const log = createLogger({ service: 'unit-test', level: 'debug' });
    expect(log.level).toBe('debug');
    expect(typeof log.info).toBe('function');
    expect(typeof log.error).toBe('function');
  });

  it('defaults the level to info when unset', () => {
    const original = process.env.LOG_LEVEL;
    delete process.env.LOG_LEVEL;
    try {
      expect(createLogger({ service: 's' }).level).toBe('info');
    } finally {
      if (original !== undefined) process.env.LOG_LEVEL = original;
    }
  });

  it('supports child loggers', () => {
    const child = createLogger({ service: 's' }).child({ requestId: 'abc' });
    expect(typeof child.info).toBe('function');
  });
});
