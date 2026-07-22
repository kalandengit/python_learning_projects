/** DI token for the resolved {@link AuthOptions}. */
export const AUTH_OPTIONS = 'AUTH_OPTIONS';

/** DI token for the {@link TokenVerifier} instance. */
export const TOKEN_VERIFIER = 'TOKEN_VERIFIER';

/**
 * Configuration for the auth layer. Values originate from the environment
 * (Twelve-Factor); no secrets are embedded. `jwksUri` defaults to the standard
 * OIDC discovery path when omitted.
 */
export interface AuthOptions {
  /** Expected token issuer (`iss`), e.g. the Keycloak realm URL. */
  issuer: string;
  /** Expected audience (`aud`) — this service's client id / API identifier. */
  audience: string;
  /** JWKS endpoint used to fetch signing keys. */
  jwksUri: string;
  /** Claim carrying the tenant id (default `tenant_id`). */
  tenantClaim: string;
  /**
   * Client id whose `resource_access[clientId].roles` are merged into the
   * principal's roles, in addition to realm roles.
   */
  clientId?: string;
  /**
   * When false, the auth guard is bypassed entirely (local development only).
   * Never enable-by-disabling in production.
   */
  enabled: boolean;
}
