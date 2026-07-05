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

## Before production (TODO)
- [ ] Replace TypeORM `synchronize` with versioned migrations.
- [ ] Add refresh-token rotation and token revocation/blacklist.
- [ ] Add a secrets manager (AWS Secrets Manager / GCP Secret Manager / Vault).
- [ ] Add centralised observability (metrics, tracing, alerting) and audit logging.
- [ ] Add automated dependency and container scanning (Dependabot, Trivy).
