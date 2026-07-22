# @asa/service-template

Golden NestJS service template for the AI School Assistant platform. Copy this
directory as the starting point for every new backend bounded context so all
services share the same production-ready cross-cutting behavior.

## What you get

- **Config** — fail-fast, zod-validated environment loading (`ConfigModule`,
  `APP_CONFIG` token). No implicit defaults for secrets.
- **Error model** — RFC 9457 `application/problem+json` for every error via a
  global `AllExceptionsFilter`; domain errors come from `@asa/errors`.
- **Health** — Kubernetes-style probes at `/api/v1/health/live` and
  `/api/v1/health/ready` (503 when a dependency is unhealthy).
- **Metrics** — Prometheus endpoint at `/metrics` (root, version-neutral) with
  default process metrics plus per-request count/latency via a global
  interceptor.
- **API surface** — global `api` prefix, URI versioning (`/api/v1/...`), strict
  `ValidationPipe` (whitelist + forbid unknown), helmet security headers,
  OpenAPI docs at `/api/docs` (non-production only).
- **Pagination** — shared `Page<T>` envelope and safe input normalization from
  `@asa/contracts`, demonstrated by the `examples` resource.
- **Auth** — OIDC/OAuth 2.1 via `@asa/auth`: deny-by-default authentication,
  RBAC (`@Roles`), `@Public` opt-outs (health, metrics), `@CurrentUser` /
  `@CurrentTenant`, and an `AsyncLocalStorage` request context (tenant +
  correlation id). The `examples` admin route and `/api/v1/me` demonstrate it.

## Layout

```
src/
  common/          global exception filter (problem+json)
  config/          env schema + config module (incl. OIDC settings)
  examples/        sample paginated resource incl. a role-guarded route
  health/          liveness/readiness probes + indicator registry (@Public)
  me/              current-principal endpoint (@CurrentUser/@CurrentTenant)
  observability/   Prometheus registry, /metrics (@Public), request interceptor
  app.module.ts    root composition (wires AuthModule.forRootAsync)
  main.ts          bootstrap + configureApp() (shared with e2e)
test/              e2e specs + auth test kit (local JWKS token signer)
```

## Development

```bash
pnpm --filter @asa/service-template build      # nest build
pnpm --filter @asa/service-template typecheck  # tsc --noEmit
pnpm --filter @asa/service-template test        # unit (jest)
pnpm --filter @asa/service-template test:e2e    # e2e (supertest)
pnpm --filter @asa/service-template start       # run compiled dist
```

## Configuration

| Variable            | Default            | Description                                     |
| ------------------- | ------------------ | ----------------------------------------------- |
| `NODE_ENV`          | `development`      | `development` \| `production` \| `test`         |
| `PORT`              | `3000`             | HTTP listen port                                |
| `LOG_LEVEL`         | `info`             | pino log level                                  |
| `SERVICE_NAME`      | `service-template` | Logged + used as the OpenAPI title              |
| `AUTH_ENABLED`      | `true`             | Auth on by default; set `false` for local dev   |
| `OIDC_ISSUER`       | —                  | Token issuer (required when auth enabled)       |
| `OIDC_AUDIENCE`     | —                  | Expected audience (required when auth enabled)  |
| `OIDC_JWKS_URI`     | —                  | JWKS endpoint (required when auth enabled)      |
| `OIDC_CLIENT_ID`    | —                  | Client whose `resource_access` roles are merged |
| `OIDC_TENANT_CLAIM` | `tenant_id`        | Claim carrying the tenant id                    |

## Extending

1. Add a feature module under `src/<feature>/` (controller + service + module).
2. Throw `@asa/errors` types for expected failures — they render as problem+json
   automatically.
3. Register dependency health via `HealthService.register(indicator)`.
4. Inject `MetricsService` for custom instruments; the request interceptor is
   already wired globally.
