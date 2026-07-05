import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GamificationModule } from './gamification/gamification.module';
import { QuizModule } from './quiz/quiz.module';
import { TajweedModule } from './tajweed/tajweed.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST ?? 'localhost',
      port: parseInt(process.env.DB_PORT ?? '5432', 10),
      username: process.env.DB_USERNAME ?? 'postgres',
      password: process.env.DB_PASSWORD ?? 'postgres',
      database: process.env.DB_NAME ?? 'ai_quran_teacher',
      autoLoadEntities: true,
      // Convenient in development; use migrations in production.
      synchronize: process.env.DB_SYNCHRONIZE === 'true',
    }),
    UsersModule,
    TajweedModule,
    QuizModule,
    GamificationModule,
  ],
})
export class AppModule {}
