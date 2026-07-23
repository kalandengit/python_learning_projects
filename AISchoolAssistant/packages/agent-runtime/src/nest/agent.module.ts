import { DynamicModule, Module, Provider } from '@nestjs/common';
import {
  AiProviderRegistry,
  EchoProvider,
  ModelRouter,
  type LanguageModelProvider,
} from '@asa/ai-sdk';
import { AgentExecutor } from '../agent-executor';
import { AgentRegistry, type AgentDefinition } from '../agent';
import {
  LoggingAgentSink,
  type AgentObservabilitySink,
} from '../observability';
import { ToolRegistry, type AgentTool } from '../tool';
import {
  AGENT_MODEL_ROUTER,
  AGENT_OBSERVABILITY,
  AGENT_PROVIDER_REGISTRY,
  AGENT_REGISTRY,
  TOOL_REGISTRY,
} from './tokens';

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Options for {@link AgentModule.forRoot}. */
export interface AgentModuleOptions {
  providers?: LanguageModelProvider[];
  aliases?: Record<string, string>;
  defaultModel?: string;
  tools?: AgentTool<any, any>[];
  agents?: AgentDefinition[];
  sink?: AgentObservabilitySink;
}

/**
 * The multi-agent runtime as a global NestJS module: a provider registry +
 * model router (AI SDK), a tool registry, an agent registry, and the
 * {@link AgentExecutor}. Features inject `AgentExecutor` and run agents by
 * id/version. Tools and agents are supplied at registration time.
 */
@Module({})
export class AgentModule {
  static forRoot(options: AgentModuleOptions = {}): DynamicModule {
    const providers: Provider[] = [
      {
        provide: AGENT_PROVIDER_REGISTRY,
        useFactory: () =>
          new AiProviderRegistry(options.providers ?? [new EchoProvider()]),
      },
      {
        provide: AGENT_MODEL_ROUTER,
        useFactory: () =>
          new ModelRouter(options.aliases ?? {}, options.defaultModel),
      },
      {
        provide: TOOL_REGISTRY,
        useFactory: () => new ToolRegistry(options.tools ?? []),
      },
      {
        provide: AGENT_REGISTRY,
        useFactory: () => new AgentRegistry(options.agents ?? []),
      },
      {
        provide: AGENT_OBSERVABILITY,
        useFactory: () => options.sink ?? new LoggingAgentSink(),
      },
      {
        provide: AgentExecutor,
        useFactory: (
          agents: AgentRegistry,
          tools: ToolRegistry,
          providerRegistry: AiProviderRegistry,
          router: ModelRouter,
          sink: AgentObservabilitySink,
        ) =>
          new AgentExecutor({
            agents,
            tools,
            providers: providerRegistry,
            router,
            sink,
          }),
        inject: [
          AGENT_REGISTRY,
          TOOL_REGISTRY,
          AGENT_PROVIDER_REGISTRY,
          AGENT_MODEL_ROUTER,
          AGENT_OBSERVABILITY,
        ],
      },
    ];

    return {
      module: AgentModule,
      global: true,
      providers,
      exports: [
        AgentExecutor,
        AGENT_REGISTRY,
        TOOL_REGISTRY,
        AGENT_PROVIDER_REGISTRY,
        AGENT_MODEL_ROUTER,
        AGENT_OBSERVABILITY,
      ],
    };
  }
}
