import { SetMetadata } from '@nestjs/common';

/** Metadata key holding the roles required to access a route. */
export const ROLES_KEY = 'asa:auth:roles';

/**
 * Require the caller to hold **all** of the given roles. Applied on top of
 * authentication; an unauthenticated caller is rejected with 401 before role
 * evaluation, a caller missing a role with 403.
 */
export const Roles = (...roles: string[]): MethodDecorator & ClassDecorator =>
  SetMetadata(ROLES_KEY, roles);
