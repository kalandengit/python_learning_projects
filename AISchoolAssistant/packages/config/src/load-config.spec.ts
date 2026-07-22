import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import { loadConfig } from './load-config';
import { ValidationError } from '@asa/errors';

const schema = z.object({
  PORT: z.coerce.number().int().default(3000),
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
  SECRET: z.string().min(8),
});

describe('loadConfig', () => {
  it('parses and coerces a valid environment', () => {
    const cfg = loadConfig(schema, {
      PORT: '8080',
      NODE_ENV: 'production',
      SECRET: 'supersecret',
    });
    expect(cfg).toEqual({
      PORT: 8080,
      NODE_ENV: 'production',
      SECRET: 'supersecret',
    });
  });

  it('applies defaults for optional values', () => {
    const cfg = loadConfig(schema, { SECRET: 'supersecret' });
    expect(cfg.PORT).toBe(3000);
    expect(cfg.NODE_ENV).toBe('development');
  });

  it('throws a ValidationError listing offending fields', () => {
    try {
      loadConfig(schema, { SECRET: 'short' });
      throw new Error('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ValidationError);
      const problem = (err as ValidationError).toProblem();
      expect(problem.status).toBe(400);
      expect(problem.errors?.some((e) => e.field === 'SECRET')).toBe(true);
    }
  });
});
