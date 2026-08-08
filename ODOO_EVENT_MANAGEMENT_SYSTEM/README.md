# EMS Enterprise — Native Odoo 19 Community v2

A native Odoo 19 Community Event Management System implemented as modular addons.

## Principles

- Extend Odoo core modules; never fork or patch Odoo core.
- Reuse `event`, `website_event`, `portal`, `payment`, and the official Stripe provider when installed.
- PostgreSQL remains the source of truth.
- Security is enforced through groups, ACLs, record rules, controller authentication, explicit state transitions and idempotency keys.
- The scanner/mobile API uses dedicated Odoo controllers and bearer/session authentication rather than exposing generic public RPC methods.
- Payment card data is never stored by EMS.

## Addons

1. `ems_core`
2. `ems_ticketing`
3. `ems_badge`
4. `ems_access`
5. `ems_waitlist`
6. `ems_seating`
7. `ems_notifications`
8. `ems_reporting`
9. `ems_gdpr`
10. `ems_website`
11. `ems_api`
12. `ems_scanner_pwa`
13. `ems_payment_stripe`
14. `ems_ai`
15. `ems_suite`

## Codex

Give Codex:

`docs/CODEX_MASTER_PROMPT_ODOO19_V2.md`

Then require it to run:

`python3 tools/validate_package.py`

and finally install the addons into a disposable Odoo 19 Community database before production deployment.
