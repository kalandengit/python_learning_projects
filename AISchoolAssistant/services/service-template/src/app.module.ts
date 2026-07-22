import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';
import { AuthModule } from '@asa/auth';
import { AllExceptionsFilter } from './common/all-exceptions.filter';
import { ConfigModule } from './config/config.module';
import { APP_CONFIG, type AppConfig, toAuthOptions } from './config/app-config';
import { ExampleModule } from './examples/example.module';
import { HealthModule } from './health/health.module';
import { MeModule } from './me/me.module';
import { MetricsModule } from './observability/metrics.module';

/**
 * Root composition. Cross-cutting concerns (config, auth, metrics) are global;
 * feature modules (health, examples, me) are imported explicitly. The global
 * exception filter renders every error as problem+json.
 */
@Module({
  imports: [
    ConfigModule,
    AuthModule.forRootAsync({
      inject: [APP_CONFIG],
      useFactory: (config: AppConfig) => toAuthOptions(config),
    }),
    MetricsModule,
    HealthModule,
    ExampleModule,
    MeModule,
  ],
  providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
