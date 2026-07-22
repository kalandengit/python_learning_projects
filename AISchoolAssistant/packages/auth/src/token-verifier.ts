import {
  createRemoteJWKSet,
  jwtVerify,
  type JWTPayload,
  type JWTVerifyGetKey,
} from 'jose';
import { UnauthorizedError } from '@asa/errors';

export interface VerifyOptions {
  issuer: string;
  audience: string;
}

/**
 * Verifies OAuth 2.1 / OIDC access tokens against a JWKS. The signing-key
 * resolver is injected so the same verification path is exercised against a
 * remote JWKS in production and a local key set in tests (no network, no
 * mocking of the crypto).
 *
 * Verification enforces signature, issuer, audience, and expiry, and pins the
 * algorithm to RS256 to prevent algorithm-substitution attacks.
 */
export class TokenVerifier {
  constructor(
    private readonly getKey: JWTVerifyGetKey,
    private readonly options: VerifyOptions,
  ) {}

  /** Build a verifier backed by a remote JWKS endpoint (production default). */
  static remote(jwksUri: string, options: VerifyOptions): TokenVerifier {
    return new TokenVerifier(createRemoteJWKSet(new URL(jwksUri)), options);
  }

  async verify(token: string): Promise<JWTPayload> {
    try {
      const { payload } = await jwtVerify(token, this.getKey, {
        issuer: this.options.issuer,
        audience: this.options.audience,
        algorithms: ['RS256'],
      });
      return payload;
    } catch {
      // Never leak the underlying reason (expired vs. bad signature vs. wrong
      // audience) to the caller; all map to an opaque 401.
      throw new UnauthorizedError('Invalid or expired access token.');
    }
  }
}
