import { Injectable } from '@nestjs/common';
import {
  Counter,
  Histogram,
  Registry,
  collectDefaultMetrics,
} from 'prom-client';

/**
 * Owns a dedicated Prometheus {@link Registry} (never the global default, so
 * tests and multiple instances stay isolated) plus the standard HTTP request
 * instruments. Default process/runtime metrics are collected too.
 */
@Injectable()
export class MetricsService {
  readonly registry: Registry;
  readonly httpRequestsTotal: Counter<string>;
  readonly httpRequestDuration: Histogram<string>;

  constructor() {
    this.registry = new Registry();
    collectDefaultMetrics({ register: this.registry });

    this.httpRequestsTotal = new Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests.',
      labelNames: ['method', 'route', 'status'],
      registers: [this.registry],
    });

    this.httpRequestDuration = new Histogram({
      name: 'http_request_duration_seconds',
      help: 'HTTP request duration in seconds.',
      labelNames: ['method', 'route', 'status'],
      buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
      registers: [this.registry],
    });
  }

  /** Record a single completed HTTP request. */
  observe(
    method: string,
    route: string,
    status: number,
    durationSeconds: number,
  ): void {
    const labels = { method, route, status: String(status) };
    this.httpRequestsTotal.inc(labels);
    this.httpRequestDuration.observe(labels, durationSeconds);
  }

  /** Serialize all metrics in the Prometheus text exposition format. */
  async render(): Promise<string> {
    return this.registry.metrics();
  }

  /** Content type for the exposition format. */
  get contentType(): string {
    return this.registry.contentType;
  }
}
