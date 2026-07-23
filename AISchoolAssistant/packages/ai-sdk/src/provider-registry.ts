import { ConflictError, NotFoundError } from '@asa/errors';
import type { LanguageModelProvider } from './provider';

/**
 * In-memory registry of model providers keyed by {@link LanguageModelProvider.id}.
 * The single lookup point the SDK uses to resolve a provider — features never
 * instantiate providers directly.
 */
export class AiProviderRegistry {
  private readonly providers = new Map<string, LanguageModelProvider>();

  constructor(providers: LanguageModelProvider[] = []) {
    for (const provider of providers) {
      this.register(provider);
    }
  }

  register(provider: LanguageModelProvider): void {
    if (this.providers.has(provider.id)) {
      throw new ConflictError(
        `Provider "${provider.id}" is already registered.`,
      );
    }
    this.providers.set(provider.id, provider);
  }

  get(id: string): LanguageModelProvider {
    const provider = this.providers.get(id);
    if (!provider) {
      throw new NotFoundError(`Provider "${id}" is not registered.`);
    }
    return provider;
  }

  has(id: string): boolean {
    return this.providers.has(id);
  }

  list(): string[] {
    return [...this.providers.keys()];
  }
}
