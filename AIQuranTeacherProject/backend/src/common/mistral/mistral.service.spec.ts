import { ConfigService } from '@nestjs/config';
import { ServiceUnavailableException } from '@nestjs/common';
import { MistralService } from './mistral.service';
import { MistralConfig } from '../../config/configuration';

const config: MistralConfig = {
  apiKey: 'test-key',
  apiUrl: 'https://api.mistral.ai/v1',
  model: 'mistral-large-latest',
  timeoutMs: 5000,
};

function makeService(overrides: Partial<MistralConfig> = {}): MistralService {
  const configService = {
    getOrThrow: () => ({ ...config, ...overrides }),
  } as unknown as ConfigService;
  return new MistralService(configService);
}

describe('MistralService', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('reports configured when an API key is present', () => {
    expect(makeService().isConfigured()).toBe(true);
    expect(makeService({ apiKey: '' }).isConfigured()).toBe(false);
  });

  it('throws ServiceUnavailable when not configured', async () => {
    const svc = makeService({ apiKey: '' });
    await expect(
      svc.chat([{ role: 'user', content: 'hi' }]),
    ).rejects.toBeInstanceOf(ServiceUnavailableException);
  });

  it('returns the assistant content on success', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        choices: [
          { message: { role: 'assistant', content: 'wa alaikum salam' } },
        ],
      }),
    }) as unknown as typeof fetch;

    const svc = makeService();
    const out = await svc.chat([{ role: 'user', content: 'salam' }]);
    expect(out).toBe('wa alaikum salam');
  });

  it('maps upstream errors to ServiceUnavailable without leaking the body', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => 'secret upstream detail',
    }) as unknown as typeof fetch;

    const svc = makeService();
    await expect(
      svc.chat([{ role: 'user', content: 'x' }]),
    ).rejects.toMatchObject({
      status: 503,
    });
  });

  it('parses JSON responses and strips markdown fences', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        choices: [
          {
            message: {
              role: 'assistant',
              content: '```json\n{"score":95}\n```',
            },
          },
        ],
      }),
    }) as unknown as typeof fetch;

    const svc = makeService();
    const out = await svc.chatJson<{ score: number }>([
      { role: 'user', content: 'x' },
    ]);
    expect(out.score).toBe(95);
  });

  it('throws on malformed JSON', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        choices: [{ message: { role: 'assistant', content: 'not json' } }],
      }),
    }) as unknown as typeof fetch;

    const svc = makeService();
    await expect(
      svc.chatJson([{ role: 'user', content: 'x' }]),
    ).rejects.toBeInstanceOf(ServiceUnavailableException);
  });
});
