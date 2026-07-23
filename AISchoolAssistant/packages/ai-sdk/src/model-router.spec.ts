import { describe, expect, it } from 'vitest';
import { ValidationError } from '@asa/errors';
import { ModelRouter } from './model-router';

describe('ModelRouter', () => {
  it('resolves a concrete provider:model reference', () => {
    const router = new ModelRouter();
    const resolved = router.resolve('anthropic:claude-sonnet-5');
    expect(resolved).toMatchObject({
      providerId: 'anthropic',
      model: 'claude-sonnet-5',
      ref: 'anthropic:claude-sonnet-5',
      requested: 'anthropic:claude-sonnet-5',
    });
  });

  it('resolves an alias to its concrete target', () => {
    const router = new ModelRouter({ fast: 'echo:default' });
    const resolved = router.resolve('fast');
    expect(resolved.providerId).toBe('echo');
    expect(resolved.model).toBe('default');
    expect(resolved.requested).toBe('fast');
  });

  it('falls back to the default when no reference is given', () => {
    const router = new ModelRouter({}, 'echo:default');
    expect(router.resolve().model).toBe('default');
  });

  it('throws when nothing resolves', () => {
    expect(() => new ModelRouter().resolve()).toThrow(ValidationError);
  });

  it.each(['noseparator', 'trailing:', ':leading'])(
    'rejects malformed reference "%s"',
    (ref) => {
      expect(() => new ModelRouter().resolve(ref)).toThrow(ValidationError);
    },
  );
});
