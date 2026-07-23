import { DynamicModule, Module, Provider } from '@nestjs/common';
import {
  AiProviderRegistry,
  EchoProvider,
  ModelRouter,
  type LanguageModelProvider,
} from '@asa/ai-sdk';
/* eslint-disable @typescript-eslint/no-explicit-any */
import type { CapabilityDefinition } from '../capability';
import { CapabilityExecutor } from '../capability-executor';
import { CapabilityRegistry } from '../capability-registry';
import {
  LoggingObservabilitySink,
  type AiObservabilitySink,
} from '../observability';
import { CapabilityBootstrap } from './capability-bootstrap';
import {
  AI_CAPABILITIES,
  AI_OBSERVABILITY,
  AI_PROVIDER_REGISTRY,
  CAPABILITY_REGISTRY,
  MODEL_ROUTER,
} from './tokens';

/** Options for {@link AiModule.forRoot}. */
export interface AiModuleOptions {
  /** Providers to register (defaults to a single {@link EchoProvider}). */
  providers?: LanguageModelProvider[];
  /** Model routing aliases (`alias -> provider:model`). */
  aliases?: Record<string, string>;
  /** Default model reference when a capability omits one. */
  defaultModel?: string;
  /** Capabilities registered + evaluated + published at boot. */
  capabilities?: CapabilityDefinition<any, any>[];
  /** Observability sink (defaults to a logging sink). */
  sink?: AiObservabilitySink;
}

/**
 * The AI-native core as a global NestJS module: the provider registry + model
 * router (the AI SDK) and the capability registry + executor + observability
 * (the Capability Registry). Features inject {@link CapabilityExecutor} and
 * invoke capabilities by id/version — they never see a provider directly.
 */
@Module({})
export class AiModule {
  static forRoot(options: AiModuleOptions = {}): DynamicModule {
    const providers: Provider[] = [
      {
        provide: AI_PROVIDER_REGISTRY,
        useFactory: () =>
          new AiProviderRegistry(options.providers ?? [new EchoProvider()]),
      },
      {
        provide: MODEL_ROUTER,
        useFactory: () =>
          new ModelRouter(options.aliases ?? {}, options.defaultModel),
      },
      {
        provide: CAPABILITY_REGISTRY,
        useFactory: () => new CapabilityRegistry(),
      },
      {
        provide: AI_OBSERVABILITY,
        useFactory: () => options.sink ?? new LoggingObservabilitySink(),
      },
      { provide: AI_CAPABILITIES, useValue: options.capabilities ?? [] },
      {
        provide: CapabilityExecutor,
        useFactory: (
          registry: CapabilityRegistry,
          providerRegistry: AiProviderRegistry,
          router: ModelRouter,
          sink: AiObservabilitySink,
        ) =>
          new CapabilityExecutor({
            registry,
            providers: providerRegistry,
            router,
            sink,
          }),
        inject: [
          CAPABILITY_REGISTRY,
          AI_PROVIDER_REGISTRY,
          MODEL_ROUTER,
          AI_OBSERVABILITY,
        ],
      },
      CapabilityBootstrap,
    ];

    return {
      module: AiModule,
      global: true,
      providers,
      exports: [
        CapabilityExecutor,
        CAPABILITY_REGISTRY,
        AI_PROVIDER_REGISTRY,
        MODEL_ROUTER,
        AI_OBSERVABILITY,
      ],
    };
  }
}
