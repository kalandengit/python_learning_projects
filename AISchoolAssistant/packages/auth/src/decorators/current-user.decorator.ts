import { createParamDecorator, type ExecutionContext } from '@nestjs/common';
import type { HttpRequest } from '../http';
import type { Principal } from '../principal';

/**
 * Inject the authenticated {@link Principal} (or one of its properties) into a
 * handler parameter, e.g. `@CurrentUser() user: Principal` or
 * `@CurrentUser('subject') id: string`.
 */
export const CurrentUser = createParamDecorator(
  (data: keyof Principal | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest<HttpRequest>();
    const principal = request.principal;
    if (!principal) {
      return undefined;
    }
    return data ? principal[data] : principal;
  },
);
