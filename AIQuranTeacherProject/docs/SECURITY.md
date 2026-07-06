# Security Checklist

Security controls implemented across the AI Quran Teacher backend and
signaling server, mapped to common standards (OWASP Top 10, least privilege).

## Authentication & authorization
- [x] Passwords hashed with **bcrypt** (cost factor 12), never stored or logged in plaintext.
- [x] Stateless **JWT** access tokens; secret required to be ≥ 32 chars in production (fail-fast).
- [x] Global `JwtAuthGuard` — endpoints are protected unless explicitly `@Public()`.
- [x] Constant-time-ish login: a bcrypt compare runs even for unknown users to reduce user enumeration.
- [x] Resource ownership enforced (a user can only read/submit their own quizzes and history).
- [x] Signaling server verifies the same JWT during the WebSocket handshake and pins the trusted `userId`.

## Input validation & output safety (OWASP A03 Injection)
- [x] Global `ValidationPipe` with `whitelist` + `forbidNonWhitelisted` strips unknown fields.
- [x] Strong DTO constraints (email format, password complexity, array/size bounds).
- [x] ORM (TypeORM) parameterises all queries — no string-built SQL.
- [x] **AI output is validated**: scores clamped to 0–100, arrays capped, enums coerced, strings length-limited.
- [x] Signaling payloads size-limited (SDP/ICE) and room ids regex-validated.

## Transport & headers (OWASP A05 Misconfiguration)
- [x] `helmet()` sets secure HTTP headers; `X-Powered-By` disabled.
- [x] Explicit CORS allow-list; no wildcard origins in production.
- [x] TLS/WSS expected at the edge (reverse proxy).

## Rate limiting & abuse (OWASP A04/A07)
- [x] Global request throttling via `@nestjs/throttler`.
- [x] Tighter limits on auth endpoints (brute-force / credential-stuffing) and AI endpoints (cost abuse).
- [x] Live-class rooms enforce a maximum participant count.

## Secrets & configuration
- [x] All secrets read from environment; `.env` is git-ignored, `.env.example` documents keys.
- [x] Fail-fast env validation at boot (`class-validator`).
- [x] Upstream (Mistral) error bodies are logged server-side but never returned to clients.

## Error handling & logging
- [x] Global exception filter returns a consistent envelope; internal errors surface as generic 500s.
- [x] Structured logging (Nest logger / pino) without secrets or credentials.

## Supply chain & runtime
- [x] Docker image runs as a non-root user, multi-stage build, production-only deps.
- [x] Pinned dependency ranges; run `npm audit` in CI.

## JWT hardening (algorithm-confusion mitigation)
Responding to the ongoing prevalence of JWT algorithm-confusion / `none`-algorithm
forgery attacks:
- [x] **Algorithm pinned to HS256** on both signing and verification — a token
      with `alg: none` or a downgraded/substituted algorithm is rejected.
      Covered by an e2e regression test (forged `none` token → 401).
- [x] Tokens carry and are verified against a fixed **issuer** and **audience**.
- [x] Expiry enforced (`ignoreExpiration: false`); short-lived access tokens.
- [x] Strong secret required (≥ 32 chars in production, fail-fast).

## Supply-chain hardening (2026 npm attack wave)
Responding to 2026 npm compromises (axios, node-ipc, TanStack, @redhat-cloud-services /
Shai-Hulud), whose common vectors were stolen maintainer accounts and **CI/CD
credential theft**:
- [x] **Least-privilege CI**: every workflow declares `permissions: contents: read`,
      so a compromised dependency/action cannot use a write-scoped `GITHUB_TOKEN`.
- [x] **Committed lockfiles** + `npm ci` (exact, reproducible installs).
- [x] **`npm audit`** runs in CI; a patched-version `overrides` entry is used where
      an upstream pin lags (e.g. Multer).
- [x] **Dependabot** watches npm (backend + signaling) and GitHub Actions weekly.
- [ ] (Recommended) Pin third-party Actions to commit SHAs; enable npm 2FA /
      provenance and a secrets manager for deploy credentials.

## Payments (Stripe)
- [x] Card data never touches our servers — Stripe Checkout/Portal (PCI **SAQ A**).
- [x] Clients pick an allow-listed **plan**, never a price/amount (no tampering).
- [x] Webhooks verified via signature over the **raw** body; bad signature → 400.
- [x] Webhook handling is **idempotent** (safe under Stripe retries).
- [x] Idempotency key on Checkout Session creation.
- [x] Secret key server-only; only the publishable key is exposed to clients.
- [x] Premium **whitelist** is admin-only (`RolesGuard`), audited, and time-boxed.

See [`STRIPE_SECURITY.md`](./STRIPE_SECURITY.md) for the full Stripe review.

## Before production (TODO)
- [ ] Replace TypeORM `synchronize` with versioned migrations.
- [ ] Add refresh-token rotation and token revocation/blacklist.
- [ ] Add a secrets manager (AWS Secrets Manager / GCP Secret Manager / Vault).
- [ ] Add centralised observability (metrics, tracing, alerting) and audit logging.
- [ ] Add automated dependency and container scanning (Dependabot, Trivy).
