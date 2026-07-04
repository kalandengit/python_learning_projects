# Section 10 — Workflow Architecture

All state machines are authoritative: services reject transitions not shown here
(RFC 7807 `urn:ams:*:invalid-transition`). Error/exception paths are explicit.

## 10.1 Visitor pre-registration & check-in/out

```mermaid
stateDiagram-v2
  [*] --> Draft: host starts form
  Draft --> PendingApproval: submit
  Draft --> Cancelled: abandon
  PendingApproval --> Approved: policy auto-approve OR host-manager approves
  PendingApproval --> Rejected: approver rejects
  PendingApproval --> SecurityReview: screening hit
  SecurityReview --> Approved: security clears
  SecurityReview --> Rejected: security blocks
  Approved --> CheckedIn: QR scan valid + docs signed
  Approved --> Expired: window passed without arrival
  Approved --> Cancelled: host or visitor cancels
  CheckedIn --> CheckedOut: kiosk / dropbox / reception / host
  CheckedIn --> Overstay: window end + grace
  Overstay --> CheckedOut: auto-checkout + review flag
  CheckedOut --> [*]
  Rejected --> [*]
  Cancelled --> [*]
  Expired --> [*]
```

**Exception paths:** kiosk offline → reception-assisted check-in against the same visit
record (edge-cached); badge printer failure → paper pass fallback + ops alert; QR
presented outside window → deny with `OUTSIDE_SCHEDULE`, offer reception; screening hit at
check-in (list updated since approval) → block + `SecurityReview` re-entry.

```mermaid
sequenceDiagram
  autonumber
  participant V as Visitor
  participant K as Kiosk
  participant VS as visitor-service
  participant BS as badge-service
  participant NS as notification-service
  participant H as Host
  V->>K: Scan QR invite
  K->>VS: POST /v1/visits/{id}/check-in (Idempotency-Key)
  VS->>VS: Validate window, re-screen watchlist
  alt screening hit
    VS-->>K: 409 SecurityReview + call security
    VS->>NS: alert SOC
  else clear
    VS->>K: request document signatures
    V->>K: sign NDA / safety brief
    VS-->>VS: commit CheckedIn + outbox(check-in.completed)
    VS-->>K: 200 CheckInResult
    par async
      BS->>BS: consume check-in.completed, issue visitor badge
      BS-->>K: badge print job (site printer)
      NS->>H: push/email/Teams "Your visitor has arrived" (<=10 s P95)
    end
  end
```

## 10.2 Approval routing, escalation & delegation

```mermaid
stateDiagram-v2
  [*] --> Pending: request routed to stage-1 approver
  Pending --> Approved: final stage approved
  Pending --> Pending: stage approved, next stage routed
  Pending --> Rejected: any stage rejects
  Pending --> EscalatedL1: 2 h SLA breach
  EscalatedL1 --> EscalatedL2: 4 h total SLA breach
  EscalatedL1 --> Approved: fallback approver approves (final)
  EscalatedL1 --> Rejected: fallback approver rejects
  EscalatedL2 --> Approved: owner's manager decides
  EscalatedL2 --> Rejected: owner's manager rejects
  Pending --> Withdrawn: requester withdraws
  Pending --> Expired: requested window passed
  Approved --> [*]: grant provisioned (compensate and alert on provisioning failure)
  Rejected --> [*]
  Withdrawn --> [*]
  Expired --> [*]
```

**Delegation:** an active delegation re-routes `Pending` items to the delegate for its
window; delegate decisions record both identities (`decidedBy`, `onBehalfOf`); delegates
cannot re-delegate (FR-038). **Failure:** grant-provisioning failure after final approval
retries 3× with backoff, then parks as `Granted-PendingProvisioning` with an ops alert —
approval outcome is never silently lost.

## 10.3 Badge issuance / replacement / revocation

```mermaid
stateDiagram-v2
  [*] --> Requested: RequestBadge (entitlement checked)
  Requested --> Issued: IssueBadge (encode RFID / sign QR)
  Requested --> Rejected: cardholder not eligible
  Issued --> Active: ActivateBadge (first use or explicit)
  Issued --> Revoked: issuance withdrawn
  Active --> Suspended: SuspendBadge (identity disabled, investigation)
  Suspended --> Active: ReinstateBadge
  Suspended --> Revoked: RevokeBadge
  Active --> Revoked: RevokeBadge (lost, offboarded, security)
  Active --> Expired: validity window end (timer)
  Active --> Lost: ReportLost (auto-revokes)
  Lost --> Revoked: immediate
  Revoked --> [*]
  Expired --> [*]
  Rejected --> [*]
```

Replacement (FR-023) is a single command producing `BadgeReplaced` which atomically
appends `BadgeRevoked(old)` + `BadgeIssued(new)` in one stream transaction — there is no
state where both validate. **Failures:** encoder/printer error keeps the badge `Issued`
(not `Active`) with retry queue; optimistic-concurrency conflict → one reload-retry then
409; Key Vault signing outage → QR issuance degrades (RFID unaffected), alert at 2 min.

## 10.4 Physical access validation (with offline-edge fallback)

```mermaid
sequenceDiagram
  autonumber
  participant R as Reader
  participant EG as Edge Gateway (site)
  participant AC as access-control-service (cloud)
  participant DL as Decision Log
  R->>EG: credential presented (RFID/QR)
  alt cloud reachable (normal)
    EG->>AC: gRPC Validate(credRef, readerId, direction)
    AC->>AC: pipeline: credential -> cardholder -> grant -> schedule -> ABAC -> anti-passback -> capacity
    AC->>DL: append decision (reason, policyVersion)
    AC-->>EG: PERMIT / DENY + reasonCode (<200 ms P95)
  else cloud unreachable (offline mode)
    EG->>EG: validate against local signed snapshot (staleness <= 24 h)
    alt snapshot fresh enough
      EG->>EG: queue decision locally (offline=true)
    else snapshot too stale
      EG->>EG: fail-secure DENY (STALE_SNAPSHOT) on Restricted zones
    end
  end
  EG->>R: unlock / deny signal
  Note over EG,AC: on reconnect: EG uploads queued decisions,<br/>AC reconciles vs revocations since last sync,<br/>conflicts flagged to SOC (OfflineDecisionConflictFlagged)
```

## 10.5 Emergency evacuation mustering & reporting

```mermaid
sequenceDiagram
  autonumber
  participant T as Trigger (alarm / SOC / site)
  participant OS as occupancy-service
  participant EG as Edge Gateways
  participant W as Warden mobile
  participant AU as audit-service (WORM)
  T->>OS: POST /v1/sites/{id}/evacuations (step-up auth)
  OS->>EG: broadcast evacuation mode (entries freeze, readers -> muster-scan)
  OS->>OS: build muster list from occupancy projection (<=30 s)
  OS-->>W: stream muster list (SSE, offline-first cache)
  loop sweep
    W->>OS: mark person SAFE / MISSING (queued if offline, merged on sync)
    EG->>OS: muster-point badge scans -> auto-SAFE
  end
  alt all accounted
    OS->>OS: state COMPLETED
  else gaps remain
    OS->>OS: report shows N UNACCOUNTED explicitly (never hidden)
  end
  OS->>AU: post-evacuation report -> WORM archive
  OS->>EG: restore normal mode
```

**Exception paths:** cloud unreachable at trigger time → edge gateways can activate
evacuation mode site-locally and reconcile later (ADR-020); warden device offline →
local queue with last-writer-wins merge, "safe" wins ties; duplicate activation →
idempotent (single active evacuation per site, second POST returns the active one, 409
only if trigger conflicts).

<!-- SECTION 10 COMPLETE -->
