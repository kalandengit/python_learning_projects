import { Controller, Get } from '@nestjs/common';
import { RedisService } from '../common/redis.service';
import { LlmService } from '../llm/llm.service';

@Controller()
export class HealthController {
  constructor(
    private readonly redis: RedisService,
    private readonly llm: LlmService,
  ) {}

  /** Liveness probe — cheap, no external calls. */
  @Get('health')
  health() {
    return { status: 'ok', uptime: process.uptime() };
  }

  /** Readiness probe — reports which optional subsystems are wired up. */
  @Get('ready')
  ready() {
    return {
      status: 'ok',
      redis: this.redis.enabled,
      llm: this.llm.enabled,
      instance: process.env.HOSTNAME ?? 'local',
    };
  }
}
