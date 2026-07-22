# ADR-0004: Identity, access control, and multi-tenancy

- **Status:** Accepted
- **Date:** 2026-07-22
- **Context:** Codex charter (security by design, least privilege); Master Spec
  #12 (governance); WP-1 (Identity).

## Decision

Authentication and authorization are a shared, mandatory layer (`@asa/auth`)
that every service composes; features never re-implement it.

1. **Protocol** — OAuth 2.1 / OIDC with **Keycloak** as the identity provider.
   Services are resource servers that validate **JWT access tokens** against the
   realm **JWKS**. No session state is held in services (stateless, Twelve-Factor).
2. **Verification** — `jose`-based, with the algorithm **pinned to RS256** and
   issuer, audience, and expiry enforced. Verification failures are opaque (a
   generic 401; the reason is never disclosed).
3. **Authorization** — **RBAC**. Roles are read from Keycloak
   `realm_access.roles` and `resource_access[clientId].roles`; routes declare
   requirements with `@Roles(...)`. **Deny-by-default**: every route is
   authenticated unless explicitly `@Public()`.
4. **Multi-tenancy** — the tenant id travels in a configurable token claim
   (default `tenant_id`) and is exposed as the first-class isolation boundary via
   `@CurrentTenant()` and an `AsyncLocalStorage`-backed `RequestContextService`.
   Tenant-scoped data access (later WPs) MUST filter by this value.
5. **Observability** — a correlation id is established per request (honoring an
   inbound `x-correlation-id`, else generated) and propagated ambiently for
   correlated logs/traces.

## Motivation

- Centralizes the security boundary so it is reviewed, tested, and hardened once
  (secure by default, least privilege — Codex).
- Provider-standard OIDC/JWKS avoids bespoke crypto and enables SSO, token
  revocation, and federation via Keycloak.
- Ambient tenant/principal context makes tenant isolation enforceable at the
  data layer without threading arguments through every call.

## Rules (enforced)

- Business logic reads identity only from the `Principal` / request context —
  never by parsing tokens itself.
- New routes are authenticated by default; making one `@Public()` is a reviewed,
  deliberate exception (health, metrics, OIDC callbacks).
- `AUTH_ENABLED=false` is a **local-development-only** switch; CI treats enabled
  auth as the default and e2e tests run with it on.

## Alternatives considered

- **Per-service bespoke auth / API keys** — rejected: inconsistent, hard to
  govern, no SSO/federation, weak revocation.
- **Opaque tokens + introspection on every request** — rejected for the hot
  path: adds latency and a hard dependency on the IdP per call; JWKS-verified
  JWTs are stateless and cacheable. (Introspection remains available for
  high-assurance flows if needed.)
- **Session cookies** — rejected: stateful, complicates horizontal scaling and
  the mobile/API-first clients.

## Consequences

- `@asa/auth` ships the guards, decorators, verifier, and request context; the
  golden service template wires it in and demonstrates protected, role-guarded,
  and public routes plus `@CurrentUser`/`@CurrentTenant`.
- Keycloak realm/client provisioning (realms, clients, roles, tenant attribute
  mapping) is an infrastructure concern tracked for the identity rollout; the
  dev `docker-compose` already runs Keycloak 26.
- Later bounded contexts (SIS/LMS) inherit tenant isolation by consuming the
  request context; AI capabilities (ADR-0002) attach the principal/tenant to
  governance metadata and audit events.
