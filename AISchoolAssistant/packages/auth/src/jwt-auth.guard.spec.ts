import { ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { UnauthorizedError } from '@asa/errors';
import { JwtAuthGuard } from './jwt-auth.guard';
import { RequestContextService } from './request-context';
import type { TokenVerifier } from './token-verifier';
import type { AuthOptions } from './tokens';

const OPTIONS: AuthOptions = {
  issuer: 'https://issuer.test',
  audience: 'asa-api',
  jwksUri: 'https://issuer.test/jwks',
  tenantClaim: 'tenant_id',
  clientId: 'asa-api',
  enabled: true,
};

interface RequestLike {
  headers: Record<string, string | undefined>;
  principal?: unknown;
}

function contextFor(request: RequestLike): ExecutionContext {
  return {
    switchToHttp: () => ({ getRequest: () => request }),
    getHandler: () => () => undefined,
    getClass: () => class {},
  } as unknown as ExecutionContext;
}

function guardWith(
  verify: jest.Mock,
  publicRoute = false,
  options: AuthOptions = OPTIONS,
): JwtAuthGuard {
  const reflector = {
    getAllAndOverride: jest.fn().mockReturnValue(publicRoute),
  } as unknown as Reflector;
  const verifier = { verify } as unknown as TokenVerifier;
  return new JwtAuthGuard(
    reflector,
    verifier,
    options,
    new RequestContextService(),
  );
}

describe('JwtAuthGuard', () => {
  it('allows public routes without a token', async () => {
    const verify = jest.fn();
    const guard = guardWith(verify, true);
    await expect(guard.canActivate(contextFor({ headers: {} }))).resolves.toBe(
      true,
    );
    expect(verify).not.toHaveBeenCalled();
  });

  it('is inert when auth is disabled', async () => {
    const verify = jest.fn();
    const guard = guardWith(verify, false, { ...OPTIONS, enabled: false });
    await expect(guard.canActivate(contextFor({ headers: {} }))).resolves.toBe(
      true,
    );
    expect(verify).not.toHaveBeenCalled();
  });

  it('rejects a request without a bearer token', async () => {
    const guard = guardWith(jest.fn());
    await expect(
      guard.canActivate(contextFor({ headers: {} })),
    ).rejects.toBeInstanceOf(UnauthorizedError);
  });

  it('rejects a non-bearer authorization scheme', async () => {
    const guard = guardWith(jest.fn());
    await expect(
      guard.canActivate(
        contextFor({ headers: { authorization: 'Basic abc' } }),
      ),
    ).rejects.toBeInstanceOf(UnauthorizedError);
  });

  it('verifies the token and attaches the principal', async () => {
    const verify = jest.fn().mockResolvedValue({
      sub: 'user-1',
      tenant_id: 'tenant-9',
      realm_access: { roles: ['teacher'] },
    });
    const guard = guardWith(verify);
    const request: RequestLike = {
      headers: { authorization: 'Bearer good.token' },
    };

    await expect(guard.canActivate(contextFor(request))).resolves.toBe(true);
    expect(verify).toHaveBeenCalledWith('good.token');
    expect(request.principal).toMatchObject({
      subject: 'user-1',
      tenantId: 'tenant-9',
      roles: ['teacher'],
    });
  });

  it('propagates verification failures as 401', async () => {
    const verify = jest
      .fn()
      .mockRejectedValue(
        new UnauthorizedError('Invalid or expired access token.'),
      );
    const guard = guardWith(verify);
    await expect(
      guard.canActivate(
        contextFor({ headers: { authorization: 'Bearer bad' } }),
      ),
    ).rejects.toBeInstanceOf(UnauthorizedError);
  });
});
