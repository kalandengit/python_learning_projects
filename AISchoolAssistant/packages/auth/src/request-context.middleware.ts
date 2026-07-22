import { randomUUID } from 'node:crypto';
import { Injectable, NestMiddleware } from '@nestjs/common';
import type { HttpRequest, HttpResponse } from './http';
import { RequestContextService } from './request-context';

const CORRELATION_HEADER = 'x-correlation-id';

type Next = () => void;

/**
 * Establishes the {@link RequestContextService} store for the lifetime of each
 * request. Implemented as middleware (not an interceptor) so the entire
 * downstream chain — guards, interceptors, and the route handler — executes
 * inside `AsyncLocalStorage.run`, making the principal, tenant, and correlation
 * id readable ambiently at any depth. The correlation id is echoed on the
 * response for client-side tracing.
 */
@Injectable()
export class RequestContextMiddleware implements NestMiddleware {
  constructor(private readonly context: RequestContextService) {}

  use(req: HttpRequest, res: HttpResponse, next: Next): void {
    const correlationId =
      this.headerValue(req, CORRELATION_HEADER) ?? randomUUID();
    res.setHeader(CORRELATION_HEADER, correlationId);
    // The store starts without a principal; the auth guard fills it in once the
    // token is verified (both run within this same async context).
    this.context.run({ correlationId }, () => next());
  }

  private headerValue(req: HttpRequest, name: string): string | undefined {
    const value = req.headers[name];
    if (Array.isArray(value)) {
      return value[0];
    }
    return typeof value === 'string' && value.length > 0 ? value : undefined;
  }
}
