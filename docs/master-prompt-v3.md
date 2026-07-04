# EMS MASTER PROMPT v3.0 — Event Management System
**Updated:** July 2026 · Supersedes v2.0 entirely · Self-contained: paste this whole file into any new Claude / Claude Code session to continue the project.

---

## 1. PROJECT IDENTITY

Production-grade, web-based **Event Management System (EMS)**:
event planning (date/time/geo) · PQC-signed QR ticketing · Stripe payments ·
role-based badges (staff/security/contractors/VIP) · post-quantum cryptography ·
versioned API · user & group management · GDPR/PCI compliant.

**Context for the AI:** You are continuing an EXISTING project at version 3.0.
All decisions in §2 are **LOCKED** — do not re-litigate, propose alternatives, or
"improve" them unless the user explicitly asks. Build on top of them.

---

## 2. LOCKED TECHNICAL DECISIONS (v3.0 — 2026 baseline)

| Layer | Decision | Notes |
|---|---|---|
| Language/runtime | Python ≥3.13 (3.14-compatible) | uv + pyproject.toml + uv.lock — never pip/requirements.txt |
| Backend | FastAPI 0.139.x, SQLAlchemy 2.0 async, asyncpg | Pydantic v2 only (v1 deprecated) |
| Database | PostgreSQL 18 + PostGIS 3.6 | Fallback image: postgis 17-3.5 |
| Cache/sessions | Valkey 8 | Redis-compatible client (`valkey` package) |
| Passwords | **Argon2id** (m=19456, t=2, p=1) | Legacy bcrypt hashes rehash transparently on login |
| Primary auth | **Passkeys (WebAuthn)**, discoverable credentials, UV required | py_webauthn; sign_count clone detection |
| Fallback auth | Password + TOTP MFA | Account lockout: 5 fails → 15 min (Valkey) |
| Tokens | **PyJWT** RS256; access 15 min; refresh 7 d with **rotation + reuse detection** | Refresh hashes in Valkey allowlist; reuse = revoke session family |
| Payments | Stripe Checkout Sessions + verified webhooks (HMAC) | PCI DSS 4.0.1 SAQ-A — card data never touches server |
| PQC | Hybrid: **ML-DSA-65** (FIPS 204) via liboqs ≥0.12 + HMAC-SHA256 layer | ALGORITHM_ALIASES maps legacy "Dilithium3" tokens; KEM reserved: ML-KEM-768 |
| QR | segno; signed envelope `{t,e,u,ts}`; timestamp refresh ≤60 s; `Cache-Control: no-store` | No PII in QR — owner as SHA-256 hash |
| Inventory | `SELECT … FOR UPDATE` on ticket_tiers before decrement | Zero overselling — non-negotiable |
| Entry scan | Single atomic `UPDATE … WHERE status='valid' RETURNING` | Duplicate scan → 409; every scan logged (accepted AND rejected) |
| Ticket lifecycle | created → valid → used → expired → refunded | Append-only ticket_status_history |
| Badges | RBAC + zone-based ABAC (JSONB zones); MANAGEMENT_TEAM = all-access | Instant activate/deactivate toggle; validity windows |
| Pagination | Cursor-based: base64(`created_at\|id`) | Never OFFSET |
| Rate limiting | Valkey sliding-window log | 100 scans/min/device; 30 purchases/hr/user; auth endpoints per-IP |
| GDPR | Art. 15 JSON export; Art. 17 anonymization (PII scrubbed, 7-yr financial retention) | Consent flags on user model |
| Frontend | React 19 + TypeScript strict + Vite 8 + **Tailwind v4** (CSS-first, `@tailwindcss/vite`, `@theme`) | No tailwind.config.js |
| FE state/data | TanStack Query v5 (server) + Zustand 5 (client) + Zod 4 (response validation) + ky | Refresh-rotation interceptor |
| Observability | **OpenTelemetry** → OTLP collector | SLO spans: API p95<500 ms, scan<200 ms |
| Containers | Multi-stage Dockerfile: uv + liboqs 0.12.0 compiled in builder; slim runtime; non-root; HEALTHCHECK | |
| Cloud | AWS eu-west-3 (Paris): ECS Fargate, ALB+WAF, RDS Multi-AZ, ElastiCache(Valkey), S3+CloudFront, Secrets Manager | Terraform, remote state S3+lock; plan-only, human applies |
| CI/CD | GitHub Actions: ruff + mypy + pytest(≥80%) + gitleaks + Trivy(CRITICAL=block) + **SBOM CycloneDX** + **SLSA attestation** + **OIDC→AWS** | Zero long-lived cloud keys in secrets |
| Compliance | GDPR, PCI DSS 4.0.1, EU CRA (SBOM), NIS2 (audit logging), OWASP ASVS | |

---

## 3. DOMAIN MODEL (implemented)

```
organizations ─< users (roles: SUPER_ADMIN, EVENT_ORGANIZER, BOX_OFFICE_STAFF,
              │         SECURITY_GUARD, ATTENDEE; MFA, GDPR flags, anonymized_at)
              │  └─< webauthn_credentials (credential_id, public_key, sign_count)
              └─< events (starts/ends tz-aware, PostGIS POINT, geofence_radius_m,
                   │      is_published, version)
                   └─< ticket_tiers (name, price_cents [0=FREE], currency,
                        │            capacity, sold_count, sales window)
                        └─< tickets (status, qr_token, used_at, payment_id, owner_id)
                             └─< ticket_status_history (append-only audit)
payments (stripe_payment_intent_id, idempotency_key, status; NO card data)
badges (type: MANAGEMENT_TEAM|SECURITY_STAFF|CONTRACTORS|VIP_VISITORS|STANDARD_ATTENDEE,
        access_zones JSONB, nfc_uid, validity window, is_active, qr_token)
scan_logs (subject ticket|badge, result accepted|rejected|duplicate, zone,
           device_id, scanned_by, scanned_at — evacuation tracking)
```

---

## 4. API SURFACE (implemented)

```
POST /api/v1/auth/register|login|refresh|logout
POST /api/v1/auth/mfa/setup|verify
POST /api/v1/auth/passkeys/register/options|register/verify|login/options|login/verify
POST /api/v1/events · GET /api/v1/events (cursor) · GET /api/v1/events/{id}
POST /api/v1/events/{id}/tiers · POST /api/v1/events/{id}/publish
POST /api/v1/tickets/purchase (Idempotency-Key; FREE→instant, PAID→Stripe URL)
GET  /api/v1/tickets/mine · GET /api/v1/tickets/{id}/qr (PNG, no-store)
POST /api/v1/tickets/validate (scanner roles, 100/min/device)
POST /api/v1/badges · PATCH /api/v1/badges/{id}/toggle · POST /api/v1/badges/validate
POST /api/v1/webhooks/stripe (raw body, signature verified)
GET  /api/v1/users/me/export (GDPR 15) · DELETE /api/v1/users/me (GDPR 17)
GET  /health
```

Invariants for ANY new endpoint: authz/IDOR check against JWT claims (`org`, `role`),
Pydantic validation, rate limit where mutating, generic error messages
(no enumeration, no stack traces), OpenAPI auto-documented.

---

## 5. COMPLETED WORK (code exists — reference, don't regenerate)

- **Part 1** — SQL schema + Alembic baseline (all tables §3, PostGIS, indexes)
- **Part 2** — Backend core: config, async DB, security (JWT/lockout/RBAC),
  pqc.py hybrid signer, qr_service, ticket_service (atomic purchase+scan),
  stripe_service (checkout/webhooks/refunds)
- **Part 3** — All routes §4 + Pytest suite (overselling, duplicate scan, PQC tamper,
  refresh reuse, enumeration) + Locust profile (500 purchases/min target)
- **v3.0 Modernization Pack** — pyproject.toml(uv), Argon2id module, PyJWT swap,
  ML-DSA-65 rename + aliases, passkeys router + webauthn_credentials model,
  telemetry.py, Dockerfile v3, docker-compose v3 (PG18/Valkey/OTel),
  frontend package.json v3, CI workflow v3 (OIDC/SBOM/SLSA), migration checklist

---

## 6. REMAINING WORK (execute in order)

### Part 4 — React Frontend (React 19 / Vite 8 / Tailwind v4)
1. ky API client: auth header injection, 401→refresh-rotation retry, Zod parsing
2. Auth pages: passkey-first login (`@github/webauthn-json`), password+TOTP fallback, register
3. Event list (cursor infinite scroll) → event detail → tier picker
4. Purchase flow → Stripe Checkout redirect → success/cancel pages
5. My Tickets: QR PNG display, auto-refetch every 60 s, status chips
6. Organizer wizard: details → map pin (geocoding) → tiers → publish
7. Badge admin: issue form (type, zones multi-select, validity), toggle, list
8. Scanner PWA: html5-qrcode camera scan, online validate, offline IndexedDB queue + sync
9. WCAG 2.2 AA throughout; vitest for API client + purchase flow

### Part 5 — Infrastructure completion
1. Terraform modules per §2 cloud row; `terraform plan` output only — never apply
2. Alembic migration ECS one-off task; seed script (1 org/organizer/event, 3 tiers, 50 tickets)
3. deploy.yml: staging auto on main, production manual approval + SHA confirmation
4. Grafana dashboards from OTel data (SLO burn rates); CloudWatch alarms

### Part 6 — Hardening & launch
1. pre-commit: ruff, gitleaks, conventional commits
2. OWASP ZAP baseline scan vs compose stack
3. docs/RUNBOOK.md: deploy, rollback, webhook replay, 90-day key rotation, incident response
4. Launch checklist as GitHub issues

---

## 7. NON-NEGOTIABLE RULES

1. Security > convenience. Never store card data. Never log secrets, tokens, or PII.
2. Never commit: .env, *.pem, *.key. gitleaks enforces; assume it will catch you.
3. Concurrency invariants (§2 inventory + scan rows) must never be "simplified".
4. Every delivered artifact: pinned versions, error handling, tests, security notes.
5. Terraform is plan-only in automation; a human applies.
6. Ask at most ONE clarifying question if blocked; otherwise proceed and state assumptions inline.
7. Coverage ≥80%, Trivy CRITICAL = build failure, mypy strict, ruff clean — CI gates, not suggestions.

---

## 8. SUCCESS METRICS

API p95 < 500 ms · scan validation < 200 ms · 500 purchases/min sustained ·
payment success > 98% · Lighthouse > 90 · WCAG 2.2 AA · zero CRITICAL vulns ·
coverage ≥ 80% · 99.95% uptime SLA

---

## 9. SESSION STARTERS (paste after this document)

**Frontend session:**
> Read the master prompt above. Execute Part 4 items 1–5 (client → auth → events → purchase → tickets). Vite 8 + React 19 + TS strict + Tailwind v4 scaffold first. Commit per feature, vitest alongside.

**Infra session:**
> Read the master prompt above. Execute Part 5. Terraform plan-only. Start with the VPC and RDS modules, then ECS.

**Hardening session:**
> Read the master prompt above. Execute Part 6 in order. RUNBOOK.md must be operational, not aspirational — every command copy-pasteable.

**Maintenance session (any future date):**
> Read the master prompt above. Before touching code: check for newer stable versions of FastAPI, React, Vite, Tailwind, liboqs, PostgreSQL and flag (don't apply) any that would change §2. Then proceed with: [task].

---

*END OF MASTER PROMPT v3.0 — keep this file at docs/master-prompt-v3.md and referenced from CLAUDE.md.*
