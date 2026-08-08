# Security Baseline

- Explicit ACLs for every EMS model.
- Organizer record rules on event-scoped objects.
- Manager-only device management, audit and sensitive configuration.
- Scanner validation endpoints require authenticated Odoo users or bearer API tokens.
- Ticket payload signature comparison uses constant-time comparison.
- No secret appears in URLs or logs.
- CSRF remains enabled for normal HTTP forms.
- JSON-RPC scanner calls rely on authenticated Odoo routes and server-side authorization.
- Payment integration stores provider references, never PAN/CVC.
- AI sends only explicitly selected event text and is disabled by default.
- GDPR exports avoid security secrets and internal scan/device secrets.
