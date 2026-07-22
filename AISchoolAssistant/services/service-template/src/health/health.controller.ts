import { Controller, Get, HttpCode, HttpStatus, Res } from '@nestjs/common';
import type { Response } from 'express';
import {
  ApiOkResponse,
  ApiServiceUnavailableResponse,
  ApiTags,
} from '@nestjs/swagger';
import { Public } from '@asa/auth';
import type { HealthReport } from '@asa/contracts';
import { HealthService } from './health.service';

/**
 * Kubernetes-style probe endpoints. `live` maps to a liveness probe (restart
 * on failure); `ready` maps to a readiness probe (remove from the load
 * balancer while dependencies are unavailable) and returns 503 when not ready.
 */
@ApiTags('health')
@Public()
@Controller('health')
export class HealthController {
  constructor(private readonly health: HealthService) {}

  @Get('live')
  @ApiOkResponse({ description: 'Process is alive.' })
  live(): HealthReport {
    return this.health.liveness();
  }

  @Get('ready')
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: 'Service is ready to accept traffic.' })
  @ApiServiceUnavailableResponse({ description: 'Service is not ready.' })
  async ready(
    @Res({ passthrough: true }) res: Response,
  ): Promise<HealthReport> {
    const report = await this.health.readiness();
    if (report.status === 'error') {
      res.status(HttpStatus.SERVICE_UNAVAILABLE);
    }
    return report;
  }
}
