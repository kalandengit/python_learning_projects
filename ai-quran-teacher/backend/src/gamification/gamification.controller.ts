import {
  Body,
  Controller,
  DefaultValuePipe,
  Get,
  Param,
  ParseIntPipe,
  ParseUUIDPipe,
  Post,
  Query,
} from '@nestjs/common';
import { IsString, IsUUID } from 'class-validator';
import { GamificationService } from './gamification.service';

class RecordActivityDto {
  @IsUUID()
  userId: string;
}

class AwardBadgeDto {
  @IsUUID()
  userId: string;

  @IsString()
  badgeCode: string;
}

@Controller('gamification')
export class GamificationController {
  constructor(private readonly gamificationService: GamificationService) {}

  @Get('badges')
  getBadgeCatalog() {
    return this.gamificationService.getBadgeCatalog();
  }

  @Get('leaderboard')
  getLeaderboard(
    @Query('limit', new DefaultValuePipe(20), ParseIntPipe) limit: number,
  ) {
    return this.gamificationService.getLeaderboard(limit);
  }

  @Get('profile/:userId')
  getProfile(@Param('userId', ParseUUIDPipe) userId: string) {
    return this.gamificationService.getProfile(userId);
  }

  /** Records a daily practice activity and updates the streak. */
  @Post('activity')
  recordActivity(@Body() dto: RecordActivityDto) {
    return this.gamificationService.updateStreak(dto.userId);
  }

  @Post('badges/award')
  awardBadge(@Body() dto: AwardBadgeDto) {
    return this.gamificationService.awardBadge(dto.userId, dto.badgeCode);
  }
}
