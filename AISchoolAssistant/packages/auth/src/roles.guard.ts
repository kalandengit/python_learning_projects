import { CanActivate, ExecutionContext, Injectable } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ForbiddenError, UnauthorizedError } from '@asa/errors';
import { ROLES_KEY } from './decorators/roles.decorator';
import type { HttpRequest } from './http';
import { hasAllRoles } from './principal';

/**
 * Enforces `@Roles(...)` metadata. Runs after {@link JwtAuthGuard}, so a
 * principal is expected to be present; its absence on a role-guarded route is
 * treated as unauthenticated (401). A principal lacking a required role is
 * forbidden (403). Routes without role metadata are unaffected.
 */
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!required || required.length === 0) {
      return true;
    }

    const request = context.switchToHttp().getRequest<HttpRequest>();
    const principal = request.principal;
    if (!principal) {
      throw new UnauthorizedError('Authentication required.');
    }

    if (!hasAllRoles(principal, required)) {
      throw new ForbiddenError(`Requires role(s): ${required.join(', ')}.`);
    }
    return true;
  }
}
