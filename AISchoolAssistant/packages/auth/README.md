# @asa/auth

OIDC / OAuth 2.1 authentication, role-based authorization, and multi-tenant
request context for AI School Assistant NestJS services. Framework-agnostic core
(token verification, claim mapping) with a thin NestJS integration layer.

## What you get

- **`AuthModule.forRoot` / `forRootAsync`** — registers everything below as a
  global module.
- **`JwtAuthGuard`** (global) — deny-by-default authentication. Verifies the
  `Authorization: Bearer` token against the JWKS, maps claims to a `Principal`,
  and attaches it to the request and the ambient context.
- **`RolesGuard`** (global) — enforces `@Roles(...)` (requires **all** listed
  roles); 401 if unauthenticated, 403 if a role is missing.
- **Decorators** — `@Public()` (opt a route out of auth), `@Roles(...)`,
  `@CurrentUser()`, `@CurrentTenant()`.
- **`RequestContextService`** — `AsyncLocalStorage`-backed access to the current
  principal, tenant, and correlation id from any layer (established by
  `RequestContextMiddleware`).
- **`TokenVerifier`** — `jose`-based JWT verification (RS256 pinned; signature,
  issuer, audience, and expiry enforced).

## Usage

```ts
// app.module.ts
AuthModule.forRootAsync({
  inject: [APP_CONFIG],
  useFactory: (config: AppConfig) => ({
    enabled: config.AUTH_ENABLED,
    issuer: config.OIDC_ISSUER,
    audience: config.OIDC_AUDIENCE,
    jwksUri: config.OIDC_JWKS_URI,
    tenantClaim: config.OIDC_TENANT_CLAIM,
    clientId: config.OIDC_CLIENT_ID,
  }),
});
```

```ts
// a controller
@Controller('reports')
export class ReportsController {
  @Get()
  list(@CurrentTenant() tenantId: string, @CurrentUser() user: Principal) { ... }

  @Get('admin')
  @Roles('reports:admin')
  admin() { ... }
}

// a public route
@Public()
@Get('health')
health() { ... }
```

## Claim mapping (Keycloak)

- Roles: `realm_access.roles` ∪ `resource_access[clientId].roles` (de-duplicated).
- Scopes: `scope` (space-delimited).
- Tenant: the configurable `tenantClaim` (default `tenant_id`).
- Identity: `sub`, `preferred_username`, `email`.

## Testing without Keycloak

Inject a local JWKS by overriding the `TOKEN_VERIFIER` provider — the same
verification path runs against an in-process key set, so tokens can be minted in
tests (see `services/service-template/test/auth-testkit.ts`). This exercises real
signature/issuer/audience/expiry checks with no network dependency.

## Security posture

- **Deny by default** — every route requires a valid token unless `@Public()`.
- **Algorithm pinned** to RS256 (prevents `alg` substitution / `none`).
- **Opaque failures** — all verification errors surface as a generic 401; the
  reason is never leaked to the caller.
- `enabled: false` fully bypasses auth and is intended for **local development
  only** — never disable in a deployed environment.
