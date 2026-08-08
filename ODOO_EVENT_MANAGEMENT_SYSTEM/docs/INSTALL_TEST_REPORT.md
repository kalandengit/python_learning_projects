# Install & Test Report

Every command below was executed; the output shown is the output produced.

## Environment

| Item | Value |
| --- | --- |
| Odoo | 19.0.0 final, commit `4d7ef1f513155010f709884325b154b862b8c59d`, Community only |
| Python | 3.11.15 |
| PostgreSQL | 16.13 |
| Enterprise addons | none installed, none referenced |
| Demo data | disabled (`--without-demo=all`) |

Odoo was run from source with the EMS addons appended to the addons path:

```
python3 odoo19/odoo-bin \
  --addons-path="odoo19/addons,odoo19/odoo/addons,ODOO_EVENT_MANAGEMENT_SYSTEM/addons" \
  --data-dir=<scratch>/odoo-data --db_host=/var/run/postgresql
```

## 1. Static validation

```
$ python3 tools/validate_package.py
Validated 15 addons
STATIC VALIDATION: PASS
```

Note: this validator parses XML, byte-compiles Python and checks manifest
paths. It passed on the baseline package too, which did not install. It is a
smoke test, not evidence of correctness.

## 2. Clean installation on a disposable database

```
$ dropdb --if-exists ems_final
$ odoo-bin -d ems_final -i ems_suite --stop-after-init --without-demo=all --log-level=warn
INSTALL EXIT=0
```

All 15 EMS modules reach state `installed`:

```
$ psql -d ems_final -tAc "select count(*) from ir_module_module
                          where name like 'ems%' and state='installed'"
15
```

`ems_access, ems_ai, ems_api, ems_badge, ems_core, ems_gdpr, ems_notifications,
ems_payment_stripe, ems_reporting, ems_scanner_pwa, ems_seating, ems_suite,
ems_ticketing, ems_waitlist, ems_website`

## 3. Upgrade

```
$ odoo-bin -d ems_final -u ems_suite --stop-after-init --log-level=warn
UPGRADE EXIT=0
```

No errors; the upgrade is idempotent and was also re-run after the restore
drill in section 5.

## 4. Test suite

```
$ odoo-bin -d ems_final -u <all 15 ems modules> --stop-after-init \
           --test-enable --log-level=test --http-port=8169
TESTS EXIT=0
```

```
ems_access:          25 tests   1.41s   1771 queries
ems_api:             12 tests   1.60s    970 queries
ems_badge:            9 tests   0.22s    219 queries
ems_gdpr:            15 tests   0.60s    852 queries
ems_notifications:   11 tests   0.15s    229 queries
ems_payment_stripe:   8 tests   0.16s    224 queries
ems_seating:         13 tests   0.18s    296 queries
ems_ticketing:       22 tests   1.51s   1127 queries
ems_waitlist:        14 tests   0.50s    381 queries
ems_website:         12 tests   1.93s   1003 queries

0 failed, 0 error(s) of 113 tests
```

What the suite actually asserts, mapped to the Definition of Done:

| Requirement | Tests |
| --- | --- |
| ACL / record rules enforced | `test_gate_operator_cannot_write_devices_directly`, `test_non_ems_user_cannot_scan`, `test_non_ems_user_cannot_manage_tickets`, `test_plain_user_cannot_process_requests`, `test_plain_user_cannot_enroll` |
| Duplicate & offline scans idempotent | `test_duplicate_client_uid_is_idempotent`, `test_same_client_uid_on_two_devices_is_not_collapsed`, `test_replayed_envelope_on_second_gate_is_duplicate`, `test_offline_batch_is_idempotent_and_partial_safe` |
| Seat concurrency | `test_second_hold_on_live_hold_is_refused`, `test_seat_cannot_be_assigned_twice`, `test_expired_hold_cannot_be_assigned`, `test_cron_expires_stale_holds` |
| Waitlist concurrency & capacity | `test_accept_creates_registration_and_burns_token`, `test_accept_is_refused_when_event_refilled`, `test_cron_promotes_only_available_capacity`, `test_cron_promote_respects_outstanding_offers` |
| Payment transaction flow | the 8 `ems_payment_stripe` tests, incl. `test_done_transaction_marks_link_paid_and_issues_ticket` and `test_reconciliation_is_idempotent` |
| Portal never exposes another user's ticket | `test_portal_lists_only_own_tickets`, `test_portal_cannot_open_another_users_ticket`, `test_portal_cannot_fetch_another_users_qr`, `test_ticket_pages_require_authentication` |
| Scanner authentication | `test_validate_requires_authentication`, `test_validate_requires_device_secret`, `test_validate_rejects_wrong_device_secret`, `test_bearer_route_rejects_a_plain_session_fetch`, `test_bearer_route_accepts_an_api_key` |
| Credential handling | `test_qr_envelope_roundtrip`, `test_envelope_expires`, `test_tampered_payload_fails_signature`, `test_rotated_credential_invalidates_old_envelope`, `test_own_qr_is_served_as_uncacheable_png` |

### Stripe scope

`payment_stripe` is installed as a dependency, and the linkage tests drive the
transaction lifecycle through Odoo's own `payment.transaction` state machine
(`_set_done` / `_set_canceled`) using the built-in transfer provider. EMS never
calls Stripe directly and stores no card data, so there is nothing in EMS that
a live Stripe key would exercise differently. **A test-mode transaction against
Stripe's own sandbox has not been run here** — that requires Stripe test
credentials and a public callback URL, and belongs to deployment acceptance.

## 5. Backup / restore drill

Executed against the live test database. The scripts in `deploy/scripts/` wrap
these same commands with `docker compose exec`.

```
--- State before backup ---
tickets=1  zones=1  ticket_name=TKT/2026/00000167

--- 1. Backup (pg_dump -Fc) ---
a04ce2f6fd03a7c10f5e9381e90247e1bc9879b02ff36f27089c4521741c0b80  db-drill.dump

--- 2. Checksum verification ---
db-drill.dump: OK

--- 3. Simulated data loss ---
DROP TABLE ems_ticket CASCADE; DROP TABLE ems_venue_zone CASCADE;
tickets table present after drop: 0

--- 4. Restore (pg_restore --clean --if-exists --no-owner) ---
0 hard errors

--- 5. State after restore ---
tickets=1  zones=1  ticket_name=TKT/2026/00000167
```

The restored database was then proven functional, not merely populated:

```
$ odoo-bin -d ems_test -u ems_suite --stop-after-init
POST-RESTORE UPGRADE EXIT=0
```

`restore.sh` refuses to proceed when the checksum sidecar is missing, stops
Odoo before `pg_restore --clean`, and restores the filestore alongside the
database.

## 6. Deployment stack validation

```
$ deploy/scripts/validate-stack.sh

== Rendering odoo.conf from a throwaway .env ==
  OK   render-config.sh produced generated/odoo.conf
  OK   dbfilter is pinned to the configured database
  OK   database manager listing is disabled
  OK   rendered config is 0600
== render-config.sh refuses placeholder secrets ==
  OK   refused to render with a CHANGE_ME secret
== Nginx configuration ==
  NOTE host has no IPv6; testing without the listen [::] directives
  nginx: configuration file test is successful
  OK   nginx -t passed
  OK   /websocket is proxied
  OK   HSTS header present
== Compose file ==
  OK   docker compose config parsed
  OK   Odoo port is bound to loopback only
  OK   db service defined
  OK   database publishes no host port
== No committed secrets ==
  OK   no live keys or private keys in deploy/

STACK VALIDATION: PASS
```

Verified with nginx 1.24.0 and Docker Compose v5.1.1.

## What has **not** been executed here

State plainly, because the Definition of Done asks for production-readiness and
these items cannot be settled from a build container:

1. **No containers were started.** The Docker daemon is not running in this
   environment, so `docker compose config` was validated but `docker compose
   up` was not. The `odoo:19.0` image was never pulled.
2. **No TLS certificate was issued.** `install-nginx.sh` was reviewed and its
   template passes `nginx -t`, but certbot needs public DNS pointing at a real
   host. The DNS pre-check in that script is what gates it.
3. **No `/websocket` traffic was exercised end to end.** The nginx location
   block is syntactically validated; a live bus connection through the proxy
   has not been observed.
4. **No Stripe sandbox transaction** — see the note in section 4.
5. **No browser ran the PWA.** Camera capture, IndexedDB and the service worker
   are exercised by no automated test; the server side they talk to is fully
   tested, the client side is not.
6. **Odoo's own dependency pins were not used** (see
   `DEPENDENCY_VERIFICATION.md`); the production image should use the pinned
   `requirements.txt`.

Items 1–3 and 5 are deployment acceptance steps. Until they are performed on
the target VPS, this package should be described as *installs, upgrades and
passes its tests on Odoo 19.0 Community* — not as production-proven.
