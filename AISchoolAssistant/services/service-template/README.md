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

## Layout

```
src/
  common/          global exception filter (problem+json)
  config/          env schema + config module
  examples/        sample paginated resource (replace per feature)
  health/          liveness/readiness probes + indicator registry
  observability/   Prometheus registry, /metrics, request interceptor
  app.module.ts    root composition
  main.ts          bootstrap + configureApp() (shared with e2e)
test/              e2e specs
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

| Variable       | Default            | Description                             |
| -------------- | ------------------ | --------------------------------------- |
| `NODE_ENV`     | `development`      | `development` \| `production` \| `test` |
| `PORT`         | `3000`             | HTTP listen port                        |
| `LOG_LEVEL`    | `info`             | pino log level                          |
| `SERVICE_NAME` | `service-template` | Logged + used as the OpenAPI title      |

## Extending

1. Add a feature module under `src/<feature>/` (controller + service + module).
2. Throw `@asa/errors` types for expected failures — they render as problem+json
   automatically.
3. Register dependency health via `HealthService.register(indicator)`.
4. Inject `MetricsService` for custom instruments; the request interceptor is
   already wired globally.
