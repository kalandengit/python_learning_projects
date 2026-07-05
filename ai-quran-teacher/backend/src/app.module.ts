import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuthModule } from './auth/auth.module';
import { CommonModule } from './common/common.module';
import { ExamModule } from './exam/exam.module';
import { GamificationModule } from './gamification/gamification.module';
import { HealthModule } from './health/health.module';
import { LlmModule } from './llm/llm.module';
import { QuizModule } from './quiz/quiz.module';
import { TajweedModule } from './tajweed/tajweed.module';
import { TutorModule } from './tutor/tutor.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    // Rate limiting: 100 requests / minute per client by default.
    // Individual routes tighten this via @Throttle (auth, tutor).
    ThrottlerModule.forRoot([
      { ttl: 60_000, limit: Number.parseInt(process.env.RATE_LIMIT ?? '100', 10) },
    ]),
    TypeOrmModule.forRoot({
      type: 'postgres',
      // DATABASE_URL takes precedence (Heroku/RDS style); else discrete vars.
      ...(process.env.DATABASE_URL
        ? { url: process.env.DATABASE_URL }
        : {
            host: process.env.DB_HOST ?? 'localhost',
            port: parseInt(process.env.DB_PORT ?? '5432', 10),
            username: process.env.DB_USERNAME ?? 'postgres',
            password: process.env.DB_PASSWORD ?? 'postgres',
            database: process.env.DB_NAME ?? 'ai_quran_teacher',
          }),
      autoLoadEntities: true,
      synchronize: process.env.DB_SYNCHRONIZE === 'true',
      ssl:
        process.env.DB_SSL === 'true'
          ? { rejectUnauthorized: false }
          : undefined,
    }),
    CommonModule,
    LlmModule,
    HealthModule,
    AuthModule,
    UsersModule,
    TajweedModule,
    QuizModule,
    ExamModule,
    GamificationModule,
    TutorModule,
  ],
  providers: [
    // Global rate-limit guard.
    { provide: APP_GUARD, useClass: ThrottlerGuard },
  ],
})
export class AppModule {}
