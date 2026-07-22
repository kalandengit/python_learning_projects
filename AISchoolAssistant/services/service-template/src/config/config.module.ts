import { Global, Module } from '@nestjs/common';
import { APP_CONFIG, loadAppConfig } from './app-config';

/**
 * Loads and validates configuration once at bootstrap (fail-fast) and exposes
 * it under the {@link APP_CONFIG} token. Global so every module can inject it
 * without re-importing.
 */
@Global()
@Module({
  providers: [{ provide: APP_CONFIG, useFactory: () => loadAppConfig() }],
  exports: [APP_CONFIG],
})
export class ConfigModule {}
