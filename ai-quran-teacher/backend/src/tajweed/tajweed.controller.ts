import { Body, Controller, Get, Param, ParseUUIDPipe, Post } from '@nestjs/common';
import { AnalyzeTextDto, DetectMistakesDto } from './tajweed.dto';
import { TajweedService } from './tajweed.service';

@Controller('tajweed')
export class TajweedController {
  constructor(private readonly tajweedService: TajweedService) {}

  @Get('rules')
  getRules() {
    return this.tajweedService.getRules();
  }

  @Post('analyze')
  analyze(@Body() dto: AnalyzeTextDto) {
    return { occurrences: this.tajweedService.analyze(dto.text) };
  }

  @Post('detect')
  detect(@Body() dto: DetectMistakesDto) {
    return this.tajweedService.detectMistakes(
      dto.text,
      dto.ayahId,
      dto.expectedText,
      dto.userId,
    );
  }

  @Get('mistakes/:userId')
  getMistakes(@Param('userId', ParseUUIDPipe) userId: string) {
    return this.tajweedService.getMistakesForUser(userId);
  }
}
