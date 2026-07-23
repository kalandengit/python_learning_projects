import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';
import { AuthModule } from '@asa/auth';
import { AiModule } from '@asa/capability-registry';
import { AgentModule } from '@asa/agent-runtime';
import { AllExceptionsFilter } from './common/all-exceptions.filter';
import { ConfigModule } from './config/config.module';
import { APP_CONFIG, type AppConfig, toAuthOptions } from './config/app-config';
import { AiFeatureModule } from './ai/ai.feature.module';
import { faqCapability } from './ai/faq.capability';
import { AgentsFeatureModule } from './agents/agents.feature.module';
import { assistantAgent } from './agents/assistant.agent';
import { addTool } from './agents/add.tool';
import { ExampleModule } from './examples/example.module';
import { HealthModule } from './health/health.module';
import { MeModule } from './me/me.module';
import { MetricsModule } from './observability/metrics.module';

/**
 * Root composition. Cross-cutting concerns (config, auth, AI runtime, metrics)
 * are global; feature modules (health, examples, me, ai) are imported
 * explicitly. The global exception filter renders every error as problem+json.
 *
 * `AiModule.forRoot` registers, evaluates, and publishes the configured
 * capabilities at boot (fail-fast if any evaluation regresses).
 */
@Module({
  imports: [
    ConfigModule,
    AuthModule.forRootAsync({
      inject: [APP_CONFIG],
      useFactory: (config: AppConfig) => toAuthOptions(config),
    }),
    AiModule.forRoot({ capabilities: [faqCapability] }),
    AgentModule.forRoot({ tools: [addTool], agents: [assistantAgent] }),
    MetricsModule,
    HealthModule,
    ExampleModule,
    MeModule,
    AiFeatureModule,
    AgentsFeatureModule,
  ],
  providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
