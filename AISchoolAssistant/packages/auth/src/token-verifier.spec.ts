import {
  SignJWT,
  createLocalJWKSet,
  exportJWK,
  generateKeyPair,
  type JWK,
  type JWTVerifyGetKey,
  type KeyLike,
} from 'jose';
import { UnauthorizedError } from '@asa/errors';
import { TokenVerifier } from './token-verifier';

const ISSUER = 'https://issuer.test/realms/asa';
const AUDIENCE = 'asa-api';
const KID = 'test-key';

interface Keys {
  privateKey: KeyLike;
  jwks: JWTVerifyGetKey;
}

async function makeKeys(): Promise<Keys> {
  const { publicKey, privateKey } = await generateKeyPair('RS256');
  const jwk: JWK = await exportJWK(publicKey);
  jwk.kid = KID;
  jwk.alg = 'RS256';
  jwk.use = 'sig';
  return {
    privateKey,
    jwks: createLocalJWKSet({ keys: [jwk] }),
  };
}

async function sign(
  privateKey: KeyLike,
  overrides: {
    issuer?: string;
    audience?: string;
    expired?: boolean;
    claims?: Record<string, unknown>;
  } = {},
): Promise<string> {
  const token = new SignJWT({ ...overrides.claims })
    .setProtectedHeader({ alg: 'RS256', kid: KID })
    .setSubject('user-1')
    .setIssuer(overrides.issuer ?? ISSUER)
    .setAudience(overrides.audience ?? AUDIENCE);

  if (overrides.expired) {
    token.setIssuedAt(1).setExpirationTime(2);
  } else {
    token.setIssuedAt().setExpirationTime('5m');
  }
  return token.sign(privateKey);
}

describe('TokenVerifier', () => {
  let keys: Keys;
  let verifier: TokenVerifier;

  beforeAll(async () => {
    keys = await makeKeys();
    verifier = new TokenVerifier(keys.jwks, {
      issuer: ISSUER,
      audience: AUDIENCE,
    });
  });

  it('verifies a well-formed token and returns its payload', async () => {
    const token = await sign(keys.privateKey, {
      claims: { preferred_username: 'ada' },
    });
    const payload = await verifier.verify(token);
    expect(payload.sub).toBe('user-1');
    expect(payload.preferred_username).toBe('ada');
  });

  it('rejects an expired token', async () => {
    const token = await sign(keys.privateKey, { expired: true });
    await expect(verifier.verify(token)).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
  });

  it('rejects a token from the wrong issuer', async () => {
    const token = await sign(keys.privateKey, {
      issuer: 'https://evil.test',
    });
    await expect(verifier.verify(token)).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
  });

  it('rejects a token with the wrong audience', async () => {
    const token = await sign(keys.privateKey, { audience: 'other-api' });
    await expect(verifier.verify(token)).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
  });

  it('rejects a token signed by an unknown key', async () => {
    const other = await makeKeys();
    const token = await sign(other.privateKey);
    await expect(verifier.verify(token)).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
  });

  it('rejects a malformed token', async () => {
    await expect(verifier.verify('not-a-jwt')).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
  });
});
