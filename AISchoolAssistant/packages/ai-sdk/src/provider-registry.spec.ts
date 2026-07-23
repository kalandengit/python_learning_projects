import { describe, expect, it } from 'vitest';
import { ConflictError, NotFoundError } from '@asa/errors';
import { AiProviderRegistry } from './provider-registry';
import { EchoProvider } from './providers/echo-provider';

describe('AiProviderRegistry', () => {
  it('registers providers passed to the constructor', () => {
    const registry = new AiProviderRegistry([new EchoProvider()]);
    expect(registry.has('echo')).toBe(true);
    expect(registry.list()).toEqual(['echo']);
  });

  it('resolves a registered provider by id', () => {
    const provider = new EchoProvider();
    const registry = new AiProviderRegistry([provider]);
    expect(registry.get('echo')).toBe(provider);
  });

  it('throws NotFoundError for an unknown provider', () => {
    const registry = new AiProviderRegistry();
    expect(() => registry.get('missing')).toThrow(NotFoundError);
  });

  it('throws ConflictError on duplicate registration', () => {
    const registry = new AiProviderRegistry([new EchoProvider()]);
    expect(() => registry.register(new EchoProvider())).toThrow(ConflictError);
  });
});
