import { ConflictError, NotFoundError } from '@asa/errors';
import { CapabilityRegistry } from './capability-registry';
import { faqCapability, testDeps } from './testing/fixtures';

describe('CapabilityRegistry', () => {
  let registry: CapabilityRegistry;

  beforeEach(() => {
    registry = new CapabilityRegistry();
  });

  it('registers a capability as draft', () => {
    registry.register(faqCapability());
    expect(registry.status('faq-answer', '1.0.0')).toBe('draft');
  });

  it('rejects duplicate id+version registration', () => {
    registry.register(faqCapability());
    expect(() => registry.register(faqCapability())).toThrow(ConflictError);
  });

  it('throws NotFoundError for an unknown capability', () => {
    expect(() => registry.get('nope', '1.0.0')).toThrow(NotFoundError);
  });

  it('publishes a capability whose evaluation passes', async () => {
    registry.register(faqCapability());
    const report = await registry.publish('faq-answer', '1.0.0', testDeps());
    expect(report.ok).toBe(true);
    expect(registry.status('faq-answer', '1.0.0')).toBe('published');
  });

  it('refuses to publish and stays draft when evaluation fails', async () => {
    registry.register(
      faqCapability({
        evaluation: {
          minPassRate: 1,
          cases: [
            { name: 'fails', input: { question: 'x' }, assert: () => false },
          ],
        },
      }),
    );
    await expect(
      registry.publish('faq-answer', '1.0.0', testDeps()),
    ).rejects.toBeInstanceOf(ConflictError);
    expect(registry.status('faq-answer', '1.0.0')).toBe('draft');
  });

  it('registerAndPublish lists the capability as published', async () => {
    await registry.registerAndPublish(faqCapability(), testDeps());
    expect(registry.list()).toEqual([
      { id: 'faq-answer', version: '1.0.0', status: 'published' },
    ]);
  });
});
