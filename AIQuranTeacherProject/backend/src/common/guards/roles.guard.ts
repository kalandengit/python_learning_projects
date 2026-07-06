import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Injectable,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { UsersService } from '../../users/users.service';
import { UserRole } from '../../users/user.entity';
import { ROLES_KEY } from '../decorators/roles.decorator';
import { AuthenticatedUser } from '../decorators/current-user.decorator';

/**
 * Authorises a request against the roles declared with `@Roles(...)`.
 *
 * The JWT deliberately does not carry the role (so a role change takes effect
 * immediately without re-issuing tokens); the guard loads the current role
 * from the database. Runs after the global `JwtAuthGuard`.
 */
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly users: UsersService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const required = this.reflector.getAllAndOverride<UserRole[] | undefined>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],
    );
    if (!required || required.length === 0) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const current = request.user as AuthenticatedUser | undefined;
    if (!current) {
      throw new ForbiddenException('Authentication required.');
    }

    const user = await this.users.findById(current.userId);
    if (!user || !required.includes(user.role)) {
      throw new ForbiddenException('Insufficient permissions.');
    }
    return true;
  }
}
