import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { MetricsService } from './metrics.service';

/**
 * Records request count and latency for every HTTP request. Uses the matched
 * route pattern (e.g. `/api/v1/examples/:id`) rather than the raw URL to keep
 * label cardinality bounded.
 */
@Injectable()
export class MetricsInterceptor implements NestInterceptor {
  constructor(private readonly metrics: MetricsService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    if (context.getType() !== 'http') {
      return next.handle();
    }

    const http = context.switchToHttp();
    const request = http.getRequest<Request>();
    const response = http.getResponse<Response>();
    const start = process.hrtime.bigint();

    return next.handle().pipe(
      finalize(() => {
        const durationSeconds = Number(process.hrtime.bigint() - start) / 1e9;
        const route = this.routeOf(request);
        this.metrics.observe(
          request.method,
          route,
          response.statusCode,
          durationSeconds,
        );
      }),
    );
  }

  private routeOf(request: Request): string {
    const route = request.route as { path?: string } | undefined;
    if (route?.path) {
      const base = (request.baseUrl ?? '').replace(/\/$/, '');
      return `${base}${route.path}` || route.path;
    }
    return 'unknown';
  }
}
