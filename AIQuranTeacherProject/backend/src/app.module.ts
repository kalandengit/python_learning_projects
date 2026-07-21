import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { APP_FILTER, APP_GUARD } from '@nestjs/core';
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';
import { AllExceptionsFilter } from './common/filters/all-exceptions.filter';
import { JwtAuthGuard } from './common/guards/jwt-auth.guard';
import { MistralModule } from './common/mistral/mistral.module';
import { StripeModule } from './common/stripe/stripe.module';
import configuration, { ThrottleConfig } from './config/configuration';
import { validate } from './config/env.validation';
import { BillingModule } from './billing/billing.module';
import { DatabaseModule } from './database/database.module';
import { GamificationModule } from './gamification/gamification.module';
import { HealthController } from './health/health.controller';
import { QuizModule } from './quiz/quiz.module';
import { QuranModule } from './quran/quran.module';
import { TajweedModule } from './tajweed/tajweed.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      cache: true,
      load: [configuration],
      validate,
    }),
    ThrottlerModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => {
        const t = config.getOrThrow<ThrottleConfig>('throttle');
        return { throttlers: [{ ttl: t.ttlMs, limit: t.limit }] };
      },
    }),
    DatabaseModule,
    MistralModule,
    StripeModule,
    UsersModule,
    QuranModule,
    TajweedModule,
    GamificationModule,
    QuizModule,
    BillingModule,
  ],
  controllers: [HealthController],
  providers: [
    // Global guards run in declaration order: rate-limit first, then auth.
    { provide: APP_GUARD, useClass: ThrottlerGuard },
    { provide: APP_GUARD, useClass: JwtAuthGuard },
    { provide: APP_FILTER, useClass: AllExceptionsFilter },
  ],
})
export class AppModule {}
