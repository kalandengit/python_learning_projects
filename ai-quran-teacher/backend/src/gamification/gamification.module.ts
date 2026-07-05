import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GamificationController } from './gamification.controller';
import {
  LeaderboardEntry,
  Streak,
  UserBadge,
} from './gamification.entity';
import { GamificationService } from './gamification.service';

@Module({
  imports: [TypeOrmModule.forFeature([UserBadge, Streak, LeaderboardEntry])],
  controllers: [GamificationController],
  providers: [GamificationService],
  exports: [GamificationService],
})
export class GamificationModule {}
