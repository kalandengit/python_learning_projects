import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule, TypeOrmModuleOptions } from '@nestjs/typeorm';
import { DatabaseConfig } from '../config/configuration';
import { Ayah } from '../quran/entities/ayah.entity';
import { Surah } from '../quran/entities/surah.entity';
import { GamificationProfile } from '../gamification/gamification.entity';
import { Quiz, QuizAttempt } from '../quiz/quiz.entity';
import { TajweedAnalysis } from '../tajweed/tajweed.entity';
import { User } from '../users/user.entity';
import { BillingCustomer } from '../billing/billing.entity';
import { PremiumGrant } from '../billing/premium-grant.entity';

const ENTITIES = [
  User,
  Surah,
  Ayah,
  TajweedAnalysis,
  Quiz,
  QuizAttempt,
  GamificationProfile,
  BillingCustomer,
  PremiumGrant,
];

/**
 * Configures TypeORM from validated config. Defaults to an embedded SQLite
 * database so the service runs with zero external dependencies in dev/test;
 * set `DB_TYPE=postgres` (and connection details) for production.
 */
@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService): TypeOrmModuleOptions => {
        const db = config.getOrThrow<DatabaseConfig>('database');
        if (db.type === 'postgres') {
          return {
            type: 'postgres',
            url: db.url,
            host: db.url ? undefined : db.host,
            port: db.url ? undefined : db.port,
            username: db.url ? undefined : db.username,
            password: db.url ? undefined : db.password,
            database: db.url ? undefined : db.database,
            ssl: db.ssl ? { rejectUnauthorized: false } : false,
            entities: ENTITIES,
            synchronize: db.synchronize,
            autoLoadEntities: true,
          };
        }
        return {
          type: 'better-sqlite3',
          database: db.database,
          entities: ENTITIES,
          synchronize: db.synchronize,
          autoLoadEntities: true,
        };
      },
    }),
  ],
})
export class DatabaseModule {}
