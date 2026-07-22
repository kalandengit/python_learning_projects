import { Controller, Get, Header, Res, VERSION_NEUTRAL } from '@nestjs/common';
import type { Response } from 'express';
import { ApiExcludeEndpoint } from '@nestjs/swagger';
import { Public } from '@asa/auth';
import { MetricsService } from './metrics.service';

/**
 * Exposes the Prometheus scrape endpoint at `/metrics`. Version-neutral and
 * excluded from the global API prefix (see `main.ts`) so scrapers hit a stable
 * path independent of API versioning.
 */
@Public()
@Controller({ path: 'metrics', version: VERSION_NEUTRAL })
export class MetricsController {
  constructor(private readonly metrics: MetricsService) {}

  @Get()
  @ApiExcludeEndpoint()
  @Header('Cache-Control', 'no-store')
  async scrape(@Res() res: Response): Promise<void> {
    res.type(this.metrics.contentType);
    res.send(await this.metrics.render());
  }
}
