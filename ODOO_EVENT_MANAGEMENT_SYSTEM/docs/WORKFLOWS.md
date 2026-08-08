# Workflows

## Ticket

```
registration ──(auto-issue, opt-in per event)──▶ active
     │                                            │
 payment done ──────────────────────────────▶ active
                                                  ├── rotate ─▶ active (token_version+1)
                                                  ├── transfer ─▶ transferred (+ new active ticket)
                                                  ├── revoke ─▶ revoked (token_version+1)
                                                  └── scan accepted ─▶ used (used_at set)
```

`active` is the only state that issues QR envelopes. Rotation, revocation and
transfer all bump `token_version`, which invalidates every envelope already
handed out.

Auto-issuance is off by default (`ems_auto_issue_tickets`) so paid events issue
on payment rather than on registration.

## Scan

```
device enrolled (secret issued once)
        │
        ▼
device authorized for event ──▶ operator scans
        │
        ▼
  signature + expiry ──▶ ticket lookup ──▶ gate authorization
        │                                        │
        │                                  lock ticket row
        │                                        ▼
        └──────────────────────────▶ accepted | duplicate | revoked
                                     expired  | wrong_event | device_revoked | invalid
```

Every outcome writes an `ems.scan.log` row, including refusals — a revoked
device's attempts are recorded, not swallowed. Idempotency is keyed on
`(device_id, client_scan_uid)`.

## Offline sync

```
offline scan ─▶ IndexedDB queue ─▶ (connectivity restored) ─▶ batch replay
                                                                   │
                              same validator as an online scan, per-item isolated
                                                                   │
                                          server acknowledges each client_scan_uid
                                                                   │
                                      only acknowledged entries leave the queue
```

Replaying the whole queue is safe and produces identical results.

## Seat

```
available ──hold_seat (row-locked)──▶ held ──assign_to_ticket──▶ assigned
                                        │
                                        ├── action_release ──▶ released
                                        └── cron (expiry passed) ──▶ expired ──▶ available
```

Only one live hold or assignment can exist per seat. An expired hold is
refused at assignment time; the cron performs the state transition.

## Waitlist

```
waiting ──action_offer──▶ offered ──action_accept(token)──▶ accepted (+ event.registration)
   ▲                         │
   │                         ├── cron (deadline passed) ──▶ expired
   └── promotion cron        └── action_cancel ──▶ cancelled
```

The promotion cron offers only genuinely free capacity: it subtracts
outstanding offers from `seats_available`. Tokens are single-use, compared in
constant time, and cleared on accept, cancel and expiry. Acceptance re-checks
capacity, because the event can refill while an offer is outstanding.

## Payment

```
Odoo payment.transaction ──▶ done ──▶ ems.payment.link = paid ──▶ ticket issued
                          └─▶ cancel/error ──▶ ems.payment.link = cancelled
```

EMS observes Odoo's transaction lifecycle. It never calls the provider and
never stores card data.

## Notification

```
enqueue (template rendered) ──▶ pending ──▶ sent
                                   │
                                   ├── provider unconfigured ──▶ failed (immediately)
                                   └── send error ──▶ pending (backoff 2^n, ≤60 min)
                                                          └── after 5 attempts ──▶ failed
                                                                                     │
                                                                          action_retry ──▶ pending
```

Each delivery runs in its own savepoint, so one bad recipient cannot roll back
the notifications already sent in the same batch.

## GDPR

```
request created ──┬── export ──▶ done (JSON payload, no signing material)
                  │
                  └── anonymize ──┬── legal hold ──▶ rejected (recorded, with reason)
                                  ├── active tickets ──▶ refused
                                  └── otherwise ──▶ done (identifiers scrubbed,
                                                          references preserved)

retention cron (daily) ──▶ purge scan logs older than N days,
                            always skipping contacts under legal hold
```
