import { Body, Controller, Get, Post, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import { AnalyzeRecitationDto } from './dto/analyze-recitation.dto';
import { TajweedAnalysis } from './tajweed.entity';
import { TajweedService } from './tajweed.service';

@ApiTags('tajweed')
@ApiBearerAuth()
@Controller('tajweed')
export class TajweedController {
  constructor(private readonly tajweedService: TajweedService) {}

  // AI calls are expensive; cap them harder than the global limit.
  @Throttle({ default: { limit: 20, ttl: 60_000 } })
  @Post('analyze')
  @ApiOperation({
    summary: 'Analyse a recitation transcript against the reference ayah.',
  })
  analyze(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: AnalyzeRecitationDto,
  ): Promise<TajweedAnalysis> {
    return this.tajweedService.analyze(user.userId, dto);
  }

  @Get('history')
  @ApiOperation({ summary: "Return the current user's recent analyses." })
  history(
    @CurrentUser() user: AuthenticatedUser,
    @Query('limit') limit?: string,
  ): Promise<TajweedAnalysis[]> {
    const parsed = limit ? Number.parseInt(limit, 10) : 20;
    return this.tajweedService.history(user.userId, parsed);
  }
}
