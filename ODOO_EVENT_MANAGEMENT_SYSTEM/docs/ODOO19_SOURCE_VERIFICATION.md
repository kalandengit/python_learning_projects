# Odoo 19 Source Verification

Verified against official Odoo 19 documentation/source on 2026-08-08:

- `event.view_event_form` exists in the official Odoo 19 `event` addon.
- `event.group_event_user` and `event.group_event_manager` exist in the official Odoo 19 security definition.
- Odoo 19 controllers support `type='http'` and `type='jsonrpc'`; `auth='bearer'` is supported.
- Odoo 19 provides the new external JSON-2 API. EMS scanner endpoints remain internal addon controllers.
- `payment.transaction._set_done` has keyword-only `state_message` and `extra_allowed_states`; the EMS override matches that signature.
- Stripe is an Odoo-supported payment provider and EMS does not store card data.

The exact deployed Odoo image/commit must still pass runtime installation and upgrade tests before production.
