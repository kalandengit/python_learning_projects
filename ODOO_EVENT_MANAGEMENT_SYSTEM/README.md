# EMS — Event Management System on Odoo 19 Community

A native Odoo 19 Community event management system: ticketing with signed QR
access credentials, badge printing, gate check-in with offline sync, reserved
seating, waitlists, an attendee portal, a scanner PWA, payment linkage and GDPR
tooling — implemented as fifteen addons that extend Odoo rather than replace
it.

**Status:** installs, upgrades and passes 113 tests on Odoo 19.0.0 Community
(commit `4d7ef1f5`). See [`docs/INSTALL_TEST_REPORT.md`](docs/INSTALL_TEST_REPORT.md)
for exactly what was executed — and what was not.

## Principles

- Extend Odoo core; never fork or patch it. `event` and `event.registration`
  are inherited, not duplicated.
- Community only. No Enterprise dependency anywhere in the 42-module closure.
- PostgreSQL is the source of truth.
- Security through groups, ACLs, record rules, controller authentication,
  explicit state transitions and idempotency keys — not through obscurity.
- The scanner API uses dedicated controllers with per-user *and* per-device
  authorization. There is no public unauthenticated mutation endpoint.
- Card data is never stored. Odoo's `payment` module owns the provider
  lifecycle.

## Addons

| Module | Purpose |
| --- | --- |
| `ems_core` | Event extensions, venue zones, groups, record-rule baseline |
| `ems_ticketing` | Tickets, signed QR envelopes, revoke/rotate/transfer, issuance hooks |
| `ems_badge` | Badges, zone policy, printable QR badge report |
| `ems_access` | Scanner devices, enrollment secrets, check-in validation, offline sync |
| `ems_waitlist` | Waitlist with capacity-aware promotion and timed single-use offers |
| `ems_seating` | Seat maps, exclusive temporary holds, atomic assignment |
| `ems_notifications` | Queued notifications with templates, retry and backoff |
| `ems_reporting` | Check-in and ticket pivots, graphs and search views |
| `ems_gdpr` | Export, anonymization, retention policy, legal hold |
| `ems_website` | Attendee portal pages and QR delivery |
| `ems_api` | Scanner/mobile JSON-RPC API (bearer + session route families) |
| `ems_scanner_pwa` | Installable scanner: camera, IndexedDB queue, service worker |
| `ems_payment_stripe` | Links `payment.transaction` to EMS objects |
| `ems_ai` | Optional, off-by-default writing assistance |
| `ems_suite` | Installs everything above |

## Quick start (development)

```bash
# with an Odoo 19 checkout in ./odoo
python3 odoo/odoo-bin \
  --addons-path=odoo/addons,odoo/odoo/addons,$(pwd)/addons \
  -d ems_dev -i ems_suite --stop-after-init --without-demo=all
```

Then run the checks:

```bash
python3 tools/validate_package.py          # static validation
deploy/scripts/validate-stack.sh           # deployment stack, offline
python3 odoo/odoo-bin -d ems_dev -u <all ems modules> \
  --stop-after-init --test-enable          # 113 tests
```

`ems_ticketing`'s post-install hook generates a random QR signing secret, so a
fresh database works immediately and no key is ever committed.

## Production deployment

See [`deploy/README.md`](deploy/README.md). Odoo is bound to loopback and
published by the host's Nginx, so the stack coexists with other projects on the
same VPS.

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) | Every defect found in the baseline package and how it was fixed |
| [`docs/DEPENDENCY_VERIFICATION.md`](docs/DEPENDENCY_VERIFICATION.md) | Every Odoo 19 API and external ID, verified against the real checkout |
| [`docs/INSTALL_TEST_REPORT.md`](docs/INSTALL_TEST_REPORT.md) | Commands run, results, and an explicit list of what was not executed |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Authorization model, credential handling, every `sudo()` justified |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Structure, trust boundaries, key design decisions |
| [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md) | State machines for tickets, seats, waitlist, scanning, payment, GDPR |
| [`docs/PRODUCT_REQUIREMENTS.md`](docs/PRODUCT_REQUIREMENTS.md) | Functional scope and enterprise constraints |
