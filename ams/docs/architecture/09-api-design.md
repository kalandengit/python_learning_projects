# Section 9 — API Design

The authoritative OpenAPI 3.1 specification is **`api/openapi.yaml`** (26 operations,
OAuth2/OIDC, RFC 7807, cursor pagination, Idempotency-Key, 3 webhooks). This section is
the design-rules preamble that keeps the spec internally consistent.

## 9.1 API design rules

**Naming & shape**
1. Resources are plural kebab-case nouns (`/v1/access-requests`); actions that aren't CRUD
   are explicit sub-resources (`POST /v1/badges/{badgeId}/revoke`) — never verbs in query strings.
2. JSON fields are `camelCase`; timestamps are RFC 3339 UTC (`2026-07-04T09:30:00Z`);
   IDs are UUID (uuidv7) strings; enums are `SCREAMING_SNAKE` free of abbreviations.
3. Path versioning `/v1/...` (ADR-008); additive-only within a major; `Sunset` +
   `Deprecation` headers announce retirements ≥ 12 months ahead.

**Errors**
4. Every non-2xx body is RFC 7807 `application/problem+json` with `type` (URN, e.g.
   `urn:ams:badge:invalid-transition`), `title`, `status`, `detail`, `instance`, and
   `traceId`. No stack traces, no internal identifiers.
5. Status-code policy: 400 malformed syntax · 401 unauthenticated · 403 authenticated but
   denied (RBAC/ABAC) · 404 not found **or** hidden by ABAC (indistinguishable by design) ·
   409 state conflict (optimistic concurrency, invalid transition) · 422 semantically
   invalid (validation failures, idempotency payload mismatch) · 429 quota · 5xx never
   contain remediation-sensitive detail.

**Mutation semantics**
6. `Idempotency-Key` (UUID) header is **required** on every POST/PATCH (ADR-017); replays
   return the original response + `Idempotency-Replayed: true`; same key with a different
   payload → 422 `urn:ams:idempotency:payload-mismatch`.
7. Optimistic concurrency on PATCH via `If-Match` ETag where a read-modify-write race is
   possible; violation → 412.

**Collections**
8. Cursor pagination only: `page[size]` (default 25, max 200), `page[after]`,
   `page[before]`; response envelope `{ data: [...], links: { next, prev }, meta: { pageSize } }`
   (ADR-018).
9. Filtering: `filter[field]=value` (repeatable, ANDed); sorting: `sort=-createdAt,name`
   (leading `-` = desc); only indexed fields are sortable — the spec enumerates them per
   endpoint.

**Security**
10. OAuth2/OIDC via Entra ID; authorization-code + PKCE for humans, client-credentials for
    services/devices; scopes per capability (`ams.visits.write`, `ams.badges.admin`,
    `ams.audit.read`, ...). APIM validates JWTs before traffic reaches any service
    (Zero Trust PEP).
11. Webhook deliveries carry `AMS-Signature: t=<unix>, v1=<hmac-sha256>` computed over
    `t.body` with the per-subscription secret; consumers must reject skew > 5 min
    (replay protection).

## 9.2 Endpoint inventory (26 operations)

| # | Operation | Purpose |
|---|---|---|
| 1 | `POST /v1/visitors` | Pre-register a visit |
| 2 | `GET /v1/visitors` | List/search visits (cursor-paged) |
| 3 | `GET /v1/visitors/{visitId}` | Visit detail |
| 4 | `PATCH /v1/visitors/{visitId}` | Amend a pre-registration |
| 5 | `POST /v1/visits/{visitId}/check-in` | Kiosk/reception check-in |
| 6 | `POST /v1/visits/{visitId}/check-out` | Check-out |
| 7 | `POST /v1/visits/{visitId}/cancel` | Cancel a visit |
| 8 | `POST /v1/badges` | Request/issue a badge |
| 9 | `GET /v1/badges` | List/search badges |
| 10 | `GET /v1/badges/{badgeId}` | Badge detail (current state) |
| 11 | `POST /v1/badges/{badgeId}/activate` | Activate an issued badge |
| 12 | `POST /v1/badges/{badgeId}/suspend` | Suspend |
| 13 | `POST /v1/badges/{badgeId}/revoke` | Revoke |
| 14 | `POST /v1/badges/{badgeId}/replace` | Atomic revoke+reissue |
| 15 | `POST /v1/badge-validations` | Validate a badge presentation (edge) |
| 16 | `POST /v1/access-requests` | Request area access |
| 17 | `GET /v1/access-requests` | List requests |
| 18 | `GET /v1/access-requests/{requestId}` | Request detail |
| 19 | `POST /v1/access-requests/{requestId}/approve` | Approve stage |
| 20 | `POST /v1/access-requests/{requestId}/reject` | Reject |
| 21 | `POST /v1/access-requests/{requestId}/delegate` | Delegate to a colleague |
| 22 | `GET /v1/sites` | List sites |
| 23 | `GET /v1/sites/{siteId}/occupancy` | Real-time occupancy |
| 24 | `POST /v1/sites/{siteId}/evacuations` | Activate evacuation |
| 25 | `GET /v1/evacuations/{evacuationId}/muster-report` | Muster status/report |
| 26 | `GET /v1/audit-events` | Audit evidence query (cursor-paged) |
| + | `POST /v1/webhook-subscriptions` | Manage webhook subscriptions |

Webhooks defined in the spec: `check-in.completed`, `badge.issued`, `badge.revoked`.

<!-- SECTION 9 COMPLETE -->
