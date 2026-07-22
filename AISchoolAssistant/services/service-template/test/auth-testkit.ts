import {
  SignJWT,
  createLocalJWKSet,
  exportJWK,
  generateKeyPair,
  type JWK,
  type KeyLike,
} from 'jose';
import { TokenVerifier } from '@asa/auth';

export const TEST_ISSUER = 'https://issuer.test/realms/asa';
export const TEST_AUDIENCE = 'asa-api';
export const TEST_CLIENT_ID = 'asa-api';
const KID = 'e2e-key';

export interface TestKit {
  verifier: TokenVerifier;
  sign: (claims?: Record<string, unknown>) => Promise<string>;
}

/**
 * Builds a {@link TokenVerifier} backed by a locally-generated RSA key and a
 * matching token signer. Lets e2e tests exercise the real verification path
 * (signature, issuer, audience, expiry) without a Keycloak dependency.
 */
export async function createAuthTestKit(): Promise<TestKit> {
  const { publicKey, privateKey } = await generateKeyPair('RS256');
  const jwk: JWK = await exportJWK(publicKey);
  jwk.kid = KID;
  jwk.alg = 'RS256';
  jwk.use = 'sig';

  const verifier = new TokenVerifier(createLocalJWKSet({ keys: [jwk] }), {
    issuer: TEST_ISSUER,
    audience: TEST_AUDIENCE,
  });

  const sign = (claims: Record<string, unknown> = {}): Promise<string> =>
    new SignJWT({
      preferred_username: 'test-user',
      tenant_id: 'tenant-1',
      ...claims,
    })
      .setProtectedHeader({ alg: 'RS256', kid: KID })
      .setSubject((claims.sub as string) ?? 'user-1')
      .setIssuer(TEST_ISSUER)
      .setAudience(TEST_AUDIENCE)
      .setIssuedAt()
      .setExpirationTime('5m')
      .sign(privateKey as KeyLike);

  return { verifier, sign };
}
