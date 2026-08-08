# CODEX MASTER EXECUTION PROMPT — EMS Odoo 19 Community v2

You are the principal Odoo 19 Community engineer completing this repository.

## Phase 0 — Mandatory inspection

Before changing code:
1. Inspect the entire repository.
2. Inspect the installed Odoo 19 Community addons and exact external IDs.
3. Generate:
   - `docs/GAP_ANALYSIS.md`
   - `docs/DEPENDENCY_VERIFICATION.md`
   - `docs/INSTALL_TEST_REPORT.md`
4. Run `python3 tools/validate_package.py`.

## Architecture rules

- Never patch Odoo core.
- Use `_inherit`, native ORM, views, security, controllers and cron.
- Do not add Enterprise-only dependencies.
- Do not replace native Odoo Events with a parallel model.
- No wildcard CORS.
- No public unauthenticated scan mutation endpoints.
- No card data.
- No hard-coded production secret.
- Minimize `sudo()` and explain every use.
- Public model/controller methods must re-check authorization.

## Installation validation

Create a disposable Odoo 19 Community database and install:
`ems_suite`

Then upgrade it once:
`-u ems_suite`

Run all tagged tests and collect logs.

## Required completion work

### Core
Validate inherited event view external IDs against the exact Odoo 19 checkout. Finish organizer/company isolation and event constraints.

### Ticketing
Complete issuance hooks from `event.registration`, secure QR envelope tests, transfer workflow, revoke/rotate flows and portal ownership.

### Badges
Complete badge printing/report template and zone policies.

### Access
Complete device enrollment secret policy, scan validation, offline batch sync, replay resistance and concurrency tests.

### Waitlist
Complete capacity integration and automated offer expiration/promotion.

### Seating
Complete seat-map domain model, hold expiry cron and atomic assignment tests.

### Notifications
Complete providers with retry/backoff and templates. Use Odoo mail for email.

### Website/Portal
Validate Odoo 19 website/portal template inheritance and complete attendee pages.

### API
Use Odoo 19 internal controllers. `type='jsonrpc'` for structured RPC routes. Use `auth='bearer'` where suitable and supported by deployment authentication. Apply per-user/device authorization.

### Scanner PWA
Complete camera integration, IndexedDB offline queue, connectivity state, sync UI, install manifest and service worker.

### Stripe
Integrate with Odoo's official `payment` / `payment_stripe` provider. Link completed `payment.transaction` records to EMS business objects. Never call Stripe directly when Odoo already owns the provider transaction lifecycle.

### GDPR
Complete export and anonymization tests, retention policies and legal-hold behavior.

### Reporting
Add pivot/graph/search views and safe operational dashboards.

### AI
Keep optional. Use configurable provider URL/model/API key. Minimize PII and protect against prompt injection. AI must never authorize access or payments.

## Production deployment

Validate:
- Docker/Compose
- PostgreSQL
- Odoo config rendering from environment
- host Nginx coexistence with other VPS projects
- TLS
- `/websocket`
- backup/restore
- update/rollback
- log rotation
- loopback-only Odoo port

## Definition of Done

Do not claim production-ready until:
- static validator passes;
- all modules install on actual Odoo 19 Community;
- `ems_suite` upgrades cleanly;
- ACL/record-rule tests pass;
- duplicate/offline scans are idempotent;
- waitlist/seat concurrency tests pass;
- Stripe test transaction flow is validated;
- portal does not expose another user's tickets;
- scanner bearer/session authentication is validated;
- backup restore drill is documented and executed;
- Nginx test passes;
- no secret is committed;
- final report lists exact commands and results.
