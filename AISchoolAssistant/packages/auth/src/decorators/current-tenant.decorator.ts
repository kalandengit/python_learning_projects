import { createParamDecorator, type ExecutionContext } from '@nestjs/common';
import type { HttpRequest } from '../http';

/**
 * Inject the caller's tenant id into a handler parameter:
 * `@CurrentTenant() tenantId: string | undefined`. Central point for the
 * multi-tenant isolation boundary — feature code scopes queries by this value.
 */
export const CurrentTenant = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): string | undefined => {
    const request = ctx.switchToHttp().getRequest<HttpRequest>();
    return request.principal?.tenantId;
  },
);
