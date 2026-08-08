# Gap Analysis — EMS Odoo 19 Community v2

Baseline: the contents of `EMS_Odoo19_Community_Enterprise_v2_Codex.zip`
(sha256 `a6317ad86f9295a2b7e5cb6db1a308f3a7a150d984f14319ea3806926a8139af`),
committed unmodified as the first commit on this branch so every item below is
reviewable as a diff.

The baseline shipped a `STATIC_VALIDATION_REPORT.txt` reading
`STATIC VALIDATION: PASS` and a `PACKAGE_MANIFEST.json` asserting
`"payment_transaction_signature_checked": true`. Both claims were produced
without an Odoo 19 runtime. **The package did not install.** The static
validator only parses XML, compiles Python and checks that manifest paths
exist; none of the defects below are visible to it.

Severity: **S1** blocks installation or is a security defect; **S2** breaks a
documented feature at runtime; **S3** is incompleteness against the spec.

---

## Blocking defects (S1)

### GAP-01 — `res.groups.category_id` no longer exists (install failure)
`ems_core/security/ems_security.xml` created groups with `category_id`.
Odoo 19 replaced that with `privilege_id` pointing at the new
`res.groups.privilege` model. Install aborted with
`ValueError: Invalid field 'category_id' in 'res.groups'`.
**Fixed**: a `res.groups.privilege` record is created and both groups reference
it, mirroring `addons/event/security/event_security.xml`.

### GAP-02 — `EmsTicket._prepare_create_values` shadowed an ORM method
`ems_ticketing/models/ticket.py` defined `_prepare_create_values(self, vals)`.
That exact name belongs to `odoo.orm.models.BaseModel`, which calls it with a
**vals_list**. Every single ticket creation therefore crashed with
`ValueError: dictionary update sequence element #0 has length 4; 2 is required`
— meaning ticketing, check-in, badges, seating and the portal were all
non-functional.
**Fixed**: renamed to `_ems_prepare_create_values`, with a comment recording
why the name is off-limits. Covered by `test_create_assigns_sequence_and_uid`.

### GAP-03 — `res.partner.mobile` was removed in Odoo 19
`ems_gdpr` wrote `mobile: False` when anonymizing, which raises on 19. The
erasure path — the one that must not fail — was broken.
**Fixed**: field dropped; `phone` is the only phone field in 19.

### GAP-04 — `_set_canceled` override had the wrong signature
The override was `_set_canceled(self, state_message=None)` while Odoo 19 ships
`_set_canceled(self, state_message=None, extra_allowed_states=())`. Any caller
passing `extra_allowed_states` hit a `TypeError` inside payment cancellation.
The baseline manifest claimed this signature had been checked.
**Fixed**: signature matched and forwarded; regression test
`test_set_canceled_accepts_extra_allowed_states`.

### GAP-05 — `res.users.groups_id` renamed to `group_ids`
The shipped test used `groups_id`. Anything assigning groups in Python was
broken on 19.
**Fixed** throughout; the same rename applies to `ir.ui.view.groups_id`.

### GAP-06 — scan idempotency key was globally unique
`ems.scan.log` had `UNIQUE(client_scan_uid)`. Scanner devices mint their own
UIDs, so two gates producing the same local counter value would silently lose a
real check-in — and the "duplicate" test passed only because it reused one
device.
**Fixed**: `UNIQUE(device_id, client_scan_uid)`, plus
`test_same_client_uid_on_two_devices_is_not_collapsed`.

### GAP-07 — scan validation had a check-then-act race
`validate_envelope` searched for an existing log, then created one, with no
savepoint and no row lock. Two concurrent requests could both observe the
ticket as `active` and both accept it, and a concurrent duplicate raised an
unhandled `UniqueViolation` that poisoned the transaction.
**Fixed**: `SELECT … FOR UPDATE` on the ticket row before the state decision,
the whole evaluation wrapped in a savepoint, and a `UniqueViolation` resolved
by returning the winning log. Covered by the `TestScan` and `TestOfflineSync`
suites.

### GAP-08 — gate staff could not record a scan (ACL deadlock)
`validate_envelope` wrote `device.last_seen_at` as the calling user, but
`ir.model.access.csv` grants `group_ems_user` read-only access to
`ems.scanner.device`. Every scan by a non-manager raised `AccessError`.
**Fixed**: the heartbeat and the check-in transition use narrowly scoped
`sudo()` with the reason stated in-line, so the ACL stays read-only.
`test_gate_operator_cannot_write_devices_directly` pins that down.

### GAP-09 — a revoked device produced no audit record
Archiving a device (`active = False`) removed it from the default `search()`,
so `_resolve_device` raised "Unknown scanner device" instead of writing a
`device_revoked` scan log. A revoked scanner left no trace of its attempts.
**Fixed**: resolution uses `active_test=False`; the attempt is logged as
`device_revoked`.

### GAP-10 — portal ticket pages returned 403 for every attendee
Two independent faults: `ems.ticket` had no ACL for `base.group_portal`, and
the templates dereferenced `ticket.event_id.name`, which portal users cannot
read. The advertised attendee experience did not work at all.
**Fixed**: read-only portal ACL, an ownership record rule
(`partner_id = user.partner_id`), and a controller that exposes four scalar
event fields through one documented elevation instead of handing the template a
record. Seven HTTP tests cover it, including the cross-user 404 cases.

### GAP-11 — the QR credential was rendered into the page as text
`portal_ems_ticket` printed the signed envelope with `t-esc`, contradicting
`docs/SECURITY.md` ("No secret appears in URLs or logs") the moment anyone
copied or shared the page.
**Fixed**: the credential is delivered only as a PNG body from
`/my/ems/ticket/<uid>/qr.png`, re-checking ownership and sending
`Cache-Control: no-store`. It never appears in a URL, a query string or the
HTML.

### GAP-12 — the scanner PWA could not authenticate (401 by design)
The PWA called `auth='bearer'` routes with only a session cookie. Odoo 19
accepts a session on a bearer route **only** for top-level document
navigations; an XHR is rejected. The bundled scanner would have failed in
production on every call.
**Fixed**: `auth='user'` routes under `/ems/scanner/api/*` for the browser
client, bearer routes retained for API-key clients, one shared authorization
path. Both behaviours are pinned by tests, including one that asserts the
bearer route *does* reject a session fetch.

### GAP-13 — no device authentication on the scan API
Any authenticated EMS user could post check-ins for any device from anywhere;
`device_uid` was an unauthenticated claim.
**Fixed**: enrollment issues a random secret, stores only a PBKDF2-SHA256 hash
(200k rounds, per-device salt, administrator-only columns), and every API call
verifies it in constant time.

### GAP-14 — `_ensure_manage_rights` rejected the superuser
The group check had no `env.su` escape, so scheduled actions and any
`sudo()` path raised `AccessError` — the promotion cron, the retention cron and
the payment-driven issuance hook could never have run.
**Fixed**: `if self.env.su: return` in each guard, applied consistently.

---

## Runtime defects (S2)

### GAP-15 — "write state, then raise" never persisted
Three places recorded a state change and then raised `UserError`
(expired seat hold, expired waitlist offer, legal-hold rejection). Raising
rolls the transaction back, so none of those writes ever reached the database —
the audit trail was fiction.
**Fixed**: refusals either raise *without* writing and leave the transition to
the owning cron, or record the outcome and return without raising, chosen per
case. The GDPR legal-hold refusal now genuinely persists, because a refused
erasure request is exactly the thing that must leave a record.

### GAP-16 — seat holds were not exclusive
`hold_seat` did a plain `search` with no lock, so two buyers could hold the
same seat, and `assign_to_ticket` never checked for an existing assignment.
**Fixed**: `SELECT … FOR UPDATE` on the seat row, a flush before the raw SQL so
the lock and the checks agree, and an explicit already-assigned guard.

### GAP-17 — waitlist offer tokens compared with `!=`
Bearer-style tokens compared non-constant-time, never invalidated after use,
and readable by any EMS user.
**Fixed**: `secrets.compare_digest`, single-use (cleared on accept, cancel and
expiry), and the column restricted to `group_ems_user`.

### GAP-18 — one bad item aborted an entire offline batch
`sync_offline_batch` let any exception escape, so a single malformed entry
discarded a whole gate's queue.
**Fixed**: per-item isolation with a typed result row for every entry;
`test_offline_batch_is_idempotent_and_partial_safe`.

### GAP-19 — unconfigured notification channels burned the retry budget
`_send_one` raised `NotImplementedError` for SMS/push, so each one consumed
five scheduled retries before failing, and one bad recipient rolled back the
whole batch.
**Fixed**: unconfigured channels fail immediately with a clear reason, and each
delivery runs in its own savepoint.

---

## Incompleteness against the specification (S3)

| Area | Baseline | Now |
| --- | --- | --- |
| Record rules | one rule, on `ems.venue.zone` | company isolation on every EMS model, organizer-scoped modification rules with manager widening, portal ownership rule |
| Badges | model + list/form only | zone-policy constraints, validity window, `allows_zone()`, QR image, QWeb PDF report |
| Seating | model + expiry cron | seat map with zones, computed availability with a searchable state, atomic assignment, seat label on the ticket |
| Waitlist | offer/accept/expire | capacity-aware promotion cron, real `event.registration` creation on accept, single-use tokens |
| Ticketing | revoke/rotate/transfer | plus registration-event constraint, opt-in auto-issuance, `used_at`, transfer provenance |
| GDPR | export + anonymize | retention policy with a daily cron, legal hold blocking both erasure and purging, refusal to erase live tickets, export proven free of signing material |
| Notifications | email only | Odoo `mail.template` rendering, provider gate, bounded backoff, per-item savepoints, retry action |
| Reporting | one pivot + one graph | ticket and check-in pivots, graphs and search views with grouping |
| Scanner PWA | textarea + manual paste | `BarcodeDetector` camera capture with cooldown, connectivity-driven auto-sync, queue depth UI, scoped service worker, credential storage |
| Deployment | compose + scripts | log rotation (absent before), container healthchecks, pinned `dbfilter`, filestore in backups, checksum-enforced restore, pre-upgrade rollback point, offline stack validator |
| Tests | 4 tests, 2 of which failed | 113 tests, all passing |

---

## Deliberately not changed

* **`ems_ai` calls an external endpoint with `requests`.** In scope for the
  spec (optional, admin-configured, off by default, prompt-injection framing
  already present). It is not reachable from any unauthenticated path.
* **`ems_company_id` duplicates the native `event.event.company_id`.** Removing
  it would be a data migration, and every EMS record rule keys off it. Left as
  is and documented.
* **No `sk_live` / private-key scanning beyond the existing checks.** The
  validator's secret scan was kept and extended to `deploy/`.
