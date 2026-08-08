# Architecture

## Native Odoo structure

EMS is fifteen installable addons. Odoo's ORM, views, security, mail, website
layer and controllers are used natively; nothing in Odoo core is patched or
forked. `event.event` and `event.registration` are extended with `_inherit`,
never duplicated into a parallel model.

```
ems_core ──┬── ems_ticketing ──┬── ems_badge ── ems_access ──┬── ems_api ── ems_scanner_pwa
           │                   │                             └── ems_reporting
           │                   ├── ems_seating
           │                   ├── ems_website
           │                   └── ems_payment_stripe
           ├── ems_waitlist ─── ems_notifications
           ├── ems_gdpr
           └── ems_ai
                                             all of the above ── ems_suite
```

## Trust boundaries

1. Browser / attendee portal
2. Scanner client (bundled PWA, or a native app with an API key)
3. Odoo HTTP layer (routing, authentication, CSRF)
4. ORM and business services (ACLs, record rules, explicit state machines)
5. PostgreSQL
6. Payment provider (Odoo `payment` / `payment_stripe`)
7. Optional AI provider

Boundaries 1 and 2 are untrusted. Everything they submit is re-validated at
boundary 4 — the controllers add authentication, not authorization decisions.

## Key design decisions

**The ticket is the auditable credential.** `ems.ticket` carries the
identity (`public_uid`), a revocation counter (`token_version`) and a state
machine. QR envelopes are derived artefacts with a 15–300 s lifetime; the
ticket is the record of truth.

**Signing is symmetric, and deliberately swappable.** HMAC-SHA256 with a key in
`ir.config_parameter`, generated randomly at install. `get_qr_envelope` /
`verify_qr_envelope` are the only two functions that touch it, so a
KMS/HSM-backed asymmetric signer can replace the implementation behind the same
two-method interface without touching callers.

**Check-in idempotency is per device, not global.** Scanners generate their own
`client_scan_uid`; two devices legitimately produce colliding values, so the
uniqueness constraint is `(device_id, client_scan_uid)`. The alternative
silently discards real check-ins.

**Concurrency is handled with row locks, not optimism.** Ticket check-in and
seat holds both take `SELECT … FOR UPDATE` before deciding, with an explicit
flush first so the lock and the subsequent reads agree with the database. Scan
creation additionally runs inside a savepoint so a lost race returns the
winner's result instead of erroring.

**Refusals never rely on writing and raising.** A `UserError` rolls the
transaction back, so any state change made just before raising is discarded.
Where an outcome must be recorded (a legal-hold rejection), the code records it
and returns; where it need not be, the code raises and leaves the transition to
the owning cron. This distinction is load-bearing and is covered by tests.

**Authorization is layered, not duplicated.** ACLs decide *what* a group may
touch; record rules decide *which records*; a small number of documented
`sudo()` calls handle the cases where a legitimate action crosses a boundary
(the check-in heartbeat, the signing key, GDPR erasure). Group guards
short-circuit on `env.su` so crons and deliberate elevation work.

**Two API route families, one implementation.** Odoo 19's `auth='bearer'`
accepts a session only for top-level document navigations, so a browser PWA
using `fetch()` is rejected. Bearer routes serve API-key clients; `auth='user'`
routes serve the PWA; both call the same authorization and business code.

**Offline sync is a queue replay, not a special case.** The batch endpoint runs
each item through exactly the same validator as an online scan, isolates
failures per item, and is safe to replay because of the idempotency key. Server
time remains authoritative; client timestamps are recorded, not trusted.

**Payments are observed, not driven.** EMS never calls Stripe. It reacts to
`payment.transaction` reaching `done` or `cancel` and reconciles its own
`ems.payment.link`, which is what keeps card data out of the system entirely.
