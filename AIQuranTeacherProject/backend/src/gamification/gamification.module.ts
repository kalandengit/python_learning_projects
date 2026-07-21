import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from '../users/user.entity';
import { GamificationController } from './gamification.controller';
import { GamificationProfile } from './gamification.entity';
import { GamificationService } from './gamification.service';

@Module({
  // User is registered here only so the leaderboard join can resolve its
  // entity metadata; the repository itself is not injected.
  imports: [TypeOrmModule.forFeature([GamificationProfile, User])],
  controllers: [GamificationController],
  providers: [GamificationService],
  exports: [GamificationService],
})
export class GamificationModule {}
