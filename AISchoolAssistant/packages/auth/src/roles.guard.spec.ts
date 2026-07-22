import { ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ForbiddenError, UnauthorizedError } from '@asa/errors';
import { RolesGuard } from './roles.guard';
import type { Principal } from './principal';

function principal(roles: string[]): Principal {
  return {
    subject: 'user-1',
    roles,
    scopes: [],
    claims: {},
  };
}

function contextFor(
  required: string[] | undefined,
  request: { principal?: Principal },
): ExecutionContext {
  return {
    switchToHttp: () => ({ getRequest: () => request }),
    getHandler: () => () => undefined,
    getClass: () => class {},
  } as unknown as ExecutionContext;
}

function guard(required: string[] | undefined): RolesGuard {
  const reflector = {
    getAllAndOverride: jest.fn().mockReturnValue(required),
  } as unknown as Reflector;
  return new RolesGuard(reflector);
}

describe('RolesGuard', () => {
  it('allows routes without role metadata', () => {
    const g = guard(undefined);
    expect(g.canActivate(contextFor(undefined, {}))).toBe(true);
  });

  it('allows when the principal holds every required role', () => {
    const g = guard(['teacher', 'admin']);
    const ctx = contextFor(['teacher', 'admin'], {
      principal: principal(['teacher', 'admin', 'user']),
    });
    expect(g.canActivate(ctx)).toBe(true);
  });

  it('forbids when a required role is missing', () => {
    const g = guard(['admin']);
    const ctx = contextFor(['admin'], { principal: principal(['teacher']) });
    expect(() => g.canActivate(ctx)).toThrow(ForbiddenError);
  });

  it('treats a missing principal on a guarded route as unauthenticated', () => {
    const g = guard(['admin']);
    expect(() => g.canActivate(contextFor(['admin'], {}))).toThrow(
      UnauthorizedError,
    );
  });
});
