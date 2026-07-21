import { SetMetadata } from '@nestjs/common';
import { UserRole } from '../../users/user.entity';

export const ROLES_KEY = 'roles';

/**
 * Restrict a route to one or more roles. Requires {@link RolesGuard} to be
 * applied (it runs after the global JWT guard, so the user is authenticated).
 *
 * @example
 *   @Roles(UserRole.Admin)
 *   @UseGuards(RolesGuard)
 *   @Post('whitelist')
 */
export const Roles = (...roles: UserRole[]) => SetMetadata(ROLES_KEY, roles);
