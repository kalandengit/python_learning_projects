# Architecture

## Native Odoo structure

The EMS is split into installable Odoo addons. Odoo ORM, views, security, mail, website and controllers are used natively.

## Trust boundaries

1. Browser/portal
2. Scanner/mobile client
3. Odoo HTTP layer
4. ORM/business services
5. PostgreSQL
6. Payment provider
7. Optional AI provider

## Key design choices

- `event.event` and `event.registration` are extended rather than duplicated.
- `ems.ticket` is the auditable access credential object.
- Access scanning is idempotent using `client_scan_uid`.
- QR payloads are short-lived signed HMAC envelopes generated server-side; the signing secret is stored in Odoo system parameters and must be provisioned securely.
- For production at higher assurance, Codex may replace HMAC with a KMS/HSM-backed asymmetric signer behind the same service API.
- Offline scanner sync submits immutable client UUIDs and client timestamps; server time remains authoritative for final acceptance.
- Seat holds expire by cron and cannot be sold twice while a valid hold exists.
- Waitlist promotion uses controlled state changes and expiration windows.
