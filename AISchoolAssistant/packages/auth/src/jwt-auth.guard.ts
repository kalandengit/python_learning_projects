import {
  CanActivate,
  ExecutionContext,
  Inject,
  Injectable,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { UnauthorizedError } from '@asa/errors';
import { IS_PUBLIC_KEY } from './decorators/public.decorator';
import { toPrincipal } from './claims';
import type { HttpRequest } from './http';
import { RequestContextService } from './request-context';
import { TokenVerifier } from './token-verifier';
import { AUTH_OPTIONS, TOKEN_VERIFIER, type AuthOptions } from './tokens';

/**
 * Authenticates every request by default (deny-by-default). Extracts the Bearer
 * token, verifies it against the JWKS, maps claims to a {@link Principal}, and
 * attaches it to the request for downstream guards, decorators, and the request
 * context. Routes marked {@link Public} are allowed through unauthenticated.
 *
 * When `options.enabled` is false (local dev only) the guard is inert — no token
 * is required and no principal is attached.
 */
@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    @Inject(TOKEN_VERIFIER) private readonly verifier: TokenVerifier,
    @Inject(AUTH_OPTIONS) private readonly options: AuthOptions,
    private readonly context: RequestContextService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    if (this.isPublic(context) || !this.options.enabled) {
      return true;
    }

    const request = context.switchToHttp().getRequest<HttpRequest>();
    const token = this.extractBearer(request);
    if (!token) {
      throw new UnauthorizedError('Missing bearer token.');
    }

    const payload = await this.verifier.verify(token);
    const principal = toPrincipal(payload, {
      tenantClaim: this.options.tenantClaim,
      clientId: this.options.clientId,
    });
    request.principal = principal;
    // Propagate into the ambient request context for downstream layers
    // (loggers, tenant-scoped repositories) that don't see the HTTP request.
    this.context.setPrincipal(principal);
    return true;
  }

  private isPublic(context: ExecutionContext): boolean {
    return (
      this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
        context.getHandler(),
        context.getClass(),
      ]) ?? false
    );
  }

  private extractBearer(request: HttpRequest): string | undefined {
    const header = request.headers.authorization;
    if (typeof header !== 'string' || !header) {
      return undefined;
    }
    const [scheme, value] = header.split(' ');
    if (scheme?.toLowerCase() !== 'bearer' || !value) {
      return undefined;
    }
    return value.trim() || undefined;
  }
}
