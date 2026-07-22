import { Injectable } from '@nestjs/common';
import type { HealthCheck, HealthReport, HealthState } from '@asa/contracts';

/**
 * A named readiness probe. Feature modules register dependency checks
 * (database, cache, broker) by providing implementations of this interface.
 */
export interface HealthIndicator {
  readonly name: string;
  check(): Promise<HealthCheck> | HealthCheck;
}

/**
 * Aggregates liveness and readiness signals. Liveness answers "is the process
 * up?"; readiness answers "can it serve traffic?" by rolling up every
 * registered {@link HealthIndicator}. The worst individual state wins.
 */
@Injectable()
export class HealthService {
  private readonly indicators: HealthIndicator[] = [];

  register(indicator: HealthIndicator): void {
    this.indicators.push(indicator);
  }

  liveness(): HealthReport {
    return {
      status: 'ok',
      checks: [{ name: 'process', status: 'ok' }],
      timestamp: new Date().toISOString(),
    };
  }

  async readiness(): Promise<HealthReport> {
    const checks = await Promise.all(
      this.indicators.map((indicator) => this.runIndicator(indicator)),
    );
    return {
      status: this.rollup(checks),
      checks: checks.length > 0 ? checks : [{ name: 'process', status: 'ok' }],
      timestamp: new Date().toISOString(),
    };
  }

  private async runIndicator(indicator: HealthIndicator): Promise<HealthCheck> {
    try {
      return await indicator.check();
    } catch (error) {
      return {
        name: indicator.name,
        status: 'error',
        detail: error instanceof Error ? error.message : 'Check failed.',
      };
    }
  }

  private rollup(checks: HealthCheck[]): HealthState {
    if (checks.some((c) => c.status === 'error')) {
      return 'error';
    }
    if (checks.some((c) => c.status === 'degraded')) {
      return 'degraded';
    }
    return 'ok';
  }
}
