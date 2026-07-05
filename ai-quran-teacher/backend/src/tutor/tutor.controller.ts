import { Body, Controller, Get, Post } from '@nestjs/common';
import { Throttle } from '@nestjs/throttler';
import { AskTutorDto } from './tutor.dto';
import { TutorService } from './tutor.service';

@Controller('tutor')
export class TutorController {
  constructor(private readonly tutorService: TutorService) {}

  @Get('status')
  status() {
    return { available: this.tutorService.available };
  }

  /**
   * LLM calls are expensive, so this route has a tighter rate limit than the
   * global default: 10 requests per minute per client.
   */
  @Throttle({ default: { limit: 10, ttl: 60_000 } })
  @Post('ask')
  ask(@Body() dto: AskTutorDto) {
    return this.tutorService.ask(dto.question, dto.context, dto.aspects);
  }
}
