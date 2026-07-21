import { Controller, Get, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import {
  GamificationService,
  LeaderboardEntry,
  ProfileSummary,
} from './gamification.service';
import { BADGES } from './badges';

@ApiTags('gamification')
@ApiBearerAuth()
@Controller('gamification')
export class GamificationController {
  constructor(private readonly gamification: GamificationService) {}

  @Get('me')
  @ApiOperation({ summary: 'Points, streak and badges for the current user.' })
  me(@CurrentUser() user: AuthenticatedUser): Promise<ProfileSummary> {
    return this.gamification.getSummary(user.userId);
  }

  @Get('badges')
  @ApiOperation({ summary: 'List every badge available in the app.' })
  catalogue(): Array<{ id: string; name: string; description: string }> {
    return BADGES.map((b) => ({
      id: b.id,
      name: b.name,
      description: b.description,
    }));
  }

  @Get('leaderboard')
  @ApiOperation({ summary: 'Top users ranked by points.' })
  leaderboard(@Query('limit') limit?: string): Promise<LeaderboardEntry[]> {
    const parsed = limit ? Number.parseInt(limit, 10) : 10;
    return this.gamification.getLeaderboard(parsed);
  }
}
