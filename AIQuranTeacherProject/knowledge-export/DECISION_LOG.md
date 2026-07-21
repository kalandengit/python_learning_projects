# Decision Log (ADR-style)

Major engineering decisions, evidenced from the code/config unless marked _(inferred)_.

## ADR-001 — Modular NestJS monolith for the API
- **Decision:** One NestJS app with a module per feature (users, quran, tajweed, quiz, gamification, billing) rather than microservices.
- **Motivation:** Small team/scope; shared DB and auth; fastest path to a coherent, testable product.
- **Alternatives:** Microservices; serverless functions.
- **Trade-offs:** Simpler ops and transactions vs. coarser scaling granularity.
- **Consequences:** Stateless app scales horizontally as a unit; clean seams (modules) allow later extraction.

## ADR-002 — Separate Socket.IO signaling service
- **Decision:** WebRTC signaling lives in its own Node service, not in the NestJS API.
- **Motivation:** Different runtime profile (long-lived sockets, fan-out) and scaling story; keeps the API stateless.
- **Alternatives:** Nest WebSocket gateway inside the API.
- **Trade-offs:** Two deployables + shared `JWT_SECRET` vs. isolation and independent scaling.
- **Consequences:** Signaling scales separately; media stays peer-to-peer (server never handles it).

## ADR-003 — SQLite (dev/test) + PostgreSQL (prod) behind one TypeORM config
- **Decision:** `DB_TYPE` switches embedded SQLite vs. Postgres.
- **Motivation:** Zero-dependency local runs and in-memory e2e; production-grade Postgres for deploy.
- **Alternatives:** Postgres everywhere (needs a DB to run tests); an ORM-less data layer.
- **Trade-offs:** Minor dialect differences (mitigated: unix-seconds bigint for time fields) vs. huge DX win.
- **Consequences:** `npm test`/e2e run with no services; smoke test uses `:memory:`.

## ADR-004 — External integrations behind mockable services
- **Decision:** `MistralService` and `StripeService` wrap the SDK/HTTP; feature code depends on them.
- **Motivation:** Testability (inject stubs, no network), one place for keys, consistent timeout/error handling.
- **Alternatives:** Call SDKs directly in services.
- **Trade-offs:** A thin layer of indirection vs. clean unit/e2e tests and key hygiene.
- **Consequences:** All AI/billing tests run offline; missing keys degrade gracefully (503).

## ADR-005 — Never trust model/external output
- **Decision:** AI responses and webhook payloads are validated, clamped, capped, and length-limited before use/persistence.
- **Motivation:** LLMs and external callers are untrusted inputs (injection, malformed data, oversized payloads).
- **Consequences:** `sanitizeMistakes/Questions`, score clamping, quiz option/index validation; webhook signature required.

## ADR-006 — Quiz answers never leave the server; grading is server-side
- **Decision:** `correctIndex` is stored but stripped from client responses; `/submit` grades on the server.
- **Motivation:** Prevent cheating / answer leakage.
- **Consequences:** `PublicQuiz` omits answers; e2e asserts no `correctIndex` leaks.

## ADR-007 — Secure-by-default authentication
- **Decision:** Global `JwtAuthGuard`; routes must opt out with `@Public()`. bcrypt cost 12. Ownership checks return 404 for others' resources.
- **Motivation:** New endpoints are protected unless deliberately exposed; avoid enumeration.
- **Consequences:** Safer defaults; `@Public()` marks health/auth/quran read.

## ADR-008 — Pin JWT algorithm + issuer/audience
- **Decision:** HS256 pinned on sign and verify; issuer/audience set and checked.
- **Motivation:** Defeat algorithm-confusion / `none`-alg forgery (a prevalent JWT attack class).
- **Consequences:** Forged `alg:none` tokens rejected (e2e regression test); tokens bound to this service.

## ADR-009 — Stripe Checkout (hosted) + signed webhooks
- **Decision:** Use hosted Checkout/Portal; client picks an allow-listed **plan**, server resolves the **price**; webhook verified over the **raw body**; handling idempotent.
- **Motivation:** Minimise PCI scope (SAQ-A); prevent price tampering and forged "subscription active" events.
- **Alternatives:** Custom card form (larger PCI scope); trusting client success redirect (insecure).
- **Consequences:** `rawBody:true`; webhook is the source of truth for entitlement.

## ADR-010 — Unified entitlement with an admin whitelist
- **Decision:** `isPremium = active subscription OR non-expired admin grant`; grants are time-boxed and audited; admin-only via `RolesGuard` (role read live from DB, not from the JWT).
- **Motivation:** Comp access for beta/scholarship without payment; instant role changes.
- **Consequences:** `PremiumGrant` entity; `source` field distinguishes subscription vs whitelist.

## ADR-011 — Caddy + Docker Compose on a single VPS; only the edge publishes ports
- **Decision:** Compose stack (db+backend+signaling+caddy); Caddy does automatic HTTPS; app/db use `expose` (internal), only Caddy publishes 80/443.
- **Motivation:** Simple, cheap, TLS-by-default test deploy; keep DB off the internet.
- **Trade-offs:** Single-host (no HA) vs. simplicity for a test deployment.
- **Consequences:** Documented that Docker bypasses UFW for published ports and that a Linode Cloud Firewall must also allow 80/443.

## ADR-012 — Supply-chain & CI hardening
- **Decision:** Least-privilege `permissions: contents: read` on all workflows; Dependabot for npm + actions; `npm audit` in CI; Multer pinned via `overrides` to a patched release.
- **Motivation:** 2026 npm supply-chain wave (stolen maintainers, CI credential theft); Multer DoS advisories.
- **Consequences:** `npm audit` clean; automated patching; reduced blast radius if a dep/action is compromised.

## ADR-013 — NestJS 11 (current stable)
- **Decision:** Target NestJS 11 (upgraded from an initial v10 pin) after checking release status.
- **Motivation:** Stay on the supported stable line.
- **Consequences:** Adjusted for v11 typing (e.g., `@nestjs/jwt` `expiresIn` type, config v4).
