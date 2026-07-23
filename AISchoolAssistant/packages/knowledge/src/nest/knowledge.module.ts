import { DynamicModule, Module, Provider } from '@nestjs/common';
import { EchoProvider, type LanguageModelProvider } from '@asa/ai-sdk';
import { KnowledgeService } from '../knowledge-service';
import { InMemoryVectorStore, type VectorStore } from '../vector-store';
import { EMBEDDING_PROVIDER, VECTOR_STORE } from './tokens';

/** Options for {@link KnowledgeModule.forRoot}. */
export interface KnowledgeModuleOptions {
  /** Embedding provider (defaults to the deterministic {@link EchoProvider}). */
  provider?: LanguageModelProvider;
  /** Embedding model reference (`provider:model`). */
  model?: string;
  /** Vector store (defaults to the {@link InMemoryVectorStore}). */
  store?: VectorStore;
}

/**
 * The Knowledge Platform as a global NestJS module: an embedding provider (AI
 * SDK), a vector store, and the {@link KnowledgeService} that ties them
 * together. Features inject `KnowledgeService` to ingest and search.
 */
@Module({})
export class KnowledgeModule {
  static forRoot(options: KnowledgeModuleOptions = {}): DynamicModule {
    const model = options.model ?? 'echo:default';
    const providers: Provider[] = [
      {
        provide: EMBEDDING_PROVIDER,
        useFactory: () => options.provider ?? new EchoProvider(),
      },
      {
        provide: VECTOR_STORE,
        useFactory: () => options.store ?? new InMemoryVectorStore(),
      },
      {
        provide: KnowledgeService,
        useFactory: (provider: LanguageModelProvider, store: VectorStore) =>
          new KnowledgeService({ provider, store, model }),
        inject: [EMBEDDING_PROVIDER, VECTOR_STORE],
      },
    ];

    return {
      module: KnowledgeModule,
      global: true,
      providers,
      exports: [KnowledgeService, VECTOR_STORE, EMBEDDING_PROVIDER],
    };
  }
}
