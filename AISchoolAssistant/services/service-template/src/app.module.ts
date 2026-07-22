import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';
import { AllExceptionsFilter } from './common/all-exceptions.filter';
import { ConfigModule } from './config/config.module';
import { ExampleModule } from './examples/example.module';
import { HealthModule } from './health/health.module';
import { MetricsModule } from './observability/metrics.module';

/**
 * Root composition. Cross-cutting concerns (config, metrics) are global;
 * feature modules (health, examples) are imported explicitly. The global
 * exception filter renders every error as problem+json.
 */
@Module({
  imports: [ConfigModule, MetricsModule, HealthModule, ExampleModule],
  providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
