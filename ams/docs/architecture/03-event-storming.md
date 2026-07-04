# Section 3 — Event Storming

Notation used in the diagrams: `CMD:` command · `EVT:` domain event · `POL:` policy /
reaction · `RM:` read model · `EXT:` external system · `ERR:` failure / compensation path.
Principles: **EDA** (events as the integration fabric), **DDD** (commands target
aggregates), **CQRS** (read models are explicit).

## 3.1 Visitor Management flow

```mermaid
flowchart LR
  subgraph PreRegistration
    C1["CMD: RegisterVisit (Host)"] --> E1["EVT: VisitRegistered"]
    E1 --> P1["POL: Run watchlist screening"]
    P1 --> C2["CMD: RecordScreeningResult"]
    C2 --> E2["EVT: ScreeningPassed"]
    C2 --> E2X["EVT: ScreeningHit"]
    E2 --> P2["POL: Auto-approve if policy matches, else request approval"]
    P2 --> E3["EVT: VisitApproved"]
    E3 --> P3["POL: Send invite with signed QR"]
    P3 --> X1["EXT: Email provider"]
  end

  subgraph CheckIn
    C3["CMD: CheckInVisitor (Kiosk QR scan)"] --> E4["EVT: VisitorCheckedIn"]
    E4 --> P4["POL: Issue visitor badge"]
    P4 --> E5["EVT: BadgeIssued (Badge ctx)"]
    E4 --> P5["POL: Notify host"]
    P5 --> X2["EXT: Notification channels"]
  end

  subgraph CheckOut
    C4["CMD: CheckOutVisitor"] --> E6["EVT: VisitorCheckedOut"]
    E6 --> P6["POL: Revoke visitor badge"]
    P6 --> E7["EVT: BadgeRevoked (Badge ctx)"]
  end

  E2X --> P7["ERR: Visit to SecurityReview, block badge, alert SOC"]
  P7 --> X3["EXT: SOC dashboard / Sentinel"]
  C3 -.-> ERR1["ERR: QR expired or window not open -> Deny with reason, offer reception desk"]
  P4 -.-> ERR2["ERR: Badge issue fails -> compensate: revert to Approved, print fallback paper pass, raise ops alert"]
  T1["POL: Window end + grace timer"] --> E8["EVT: VisitOverstayed"]
  E8 --> P8["POL: Auto-checkout + flag for review"]
  E1 --> RM1["RM: Expected visitors today (per site)"]
  E4 --> RM2["RM: On-site visitors (occupancy)"]
  E6 --> RM2
```

**Failure/compensation paths:** screening hit → `SecurityReview` (no badge until security
clears); badge-issue failure → saga compensation back to `Approved` with manual fallback;
overstay timer → auto-checkout + review flag; kiosk offline → reception-assisted flow
(Section 10.1).

## 3.2 Badge Lifecycle flow

```mermaid
flowchart LR
  C1["CMD: RequestBadge"] --> E1["EVT: BadgeRequested"]
  E1 --> P1["POL: Verify cardholder Active + entitlement"]
  P1 --> C2["CMD: IssueBadge"]
  C2 --> E2["EVT: BadgeIssued"]
  E2 --> P2["POL: Encode RFID / sign QR"]
  P2 --> X1["EXT: Card printer / QR signer (Key Vault)"]
  E2 --> P3["POL: Publish credential to validation snapshot"]
  P3 --> RM1["RM: credential_validation_snapshot (edge cache)"]

  C3["CMD: ReportLost (self-service)"] --> E3["EVT: BadgeReportedLost"]
  E3 --> P4["POL: Immediate revoke"]
  P4 --> E4["EVT: BadgeRevoked"]
  E4 --> P3
  E3 --> P5["POL: Offer replacement"]
  P5 --> C4["CMD: ReplaceBadge"]
  C4 --> E5["EVT: BadgeReplaced (atomic revoke old + issue new)"]

  T1["POL: Validity/contract expiry timer"] --> E6["EVT: BadgeExpired"]
  E6 --> P3
  X2["EXT: Entra ID disable event"] --> P6["POL: Suspend all cardholder badges within 60s"]
  P6 --> E7["EVT: BadgeSuspended"]
  E7 --> P3

  C2 -.-> ERR1["ERR: cardholder not Active -> reject command, no event"]
  P2 -.-> ERR2["ERR: printer/encoder failure -> badge stays Issued-not-Active, retry queue, ops alert"]
  C4 -.-> ERR3["ERR: concurrency conflict (expectedVersion mismatch) -> reload stream, retry once, else 409"]
  E2 --> RM2["RM: badge_current_state"]
  E4 --> RM2
  E7 --> RM2
```

**Failure/compensation:** encoder failure leaves the badge `Issued` (not `Active`) with a
retry queue; optimistic-concurrency conflicts on the event stream retry once then surface
RFC 7807 409; revocation events always win over issuance in snapshot merge (tombstone
precedence, Section 14.3).

## 3.3 Access Approval flow

```mermaid
flowchart LR
  C1["CMD: RequestAccess (cardholder or manager)"] --> E1["EVT: ApprovalRequested"]
  E1 --> P1["POL: Resolve approval chain from area ownership"]
  P1 --> RM1["RM: Approver inbox"]
  P1 --> X1["EXT: Notification (email/Teams deep link)"]

  C2["CMD: Approve (approver)"] --> E2["EVT: ApprovalStageCompleted"]
  E2 --> P2["POL: More stages? route next : finalize"]
  P2 --> E3["EVT: ApprovalGranted"]
  E3 --> P3["POL: Provision AccessGrant (time-boxed)"]
  P3 --> E4["EVT: AccessGranted (Access ctx)"]
  E4 --> P4["POL: Push grant to site config snapshot"]
  P4 --> RM2["RM: edge policy cache"]

  C3["CMD: Reject"] --> E5["EVT: ApprovalRejected"]
  E5 --> X2["EXT: Notify requester with reason"]

  T1["POL: SLA timer 2h"] --> E6["EVT: ApprovalEscalated (level 1: fallback approver)"]
  T2["POL: SLA timer 4h"] --> E7["EVT: ApprovalEscalated (level 2: owner's manager)"]
  E6 --> RM1
  E7 --> RM1

  C4["CMD: Delegate (approver, bounded window)"] --> E8["EVT: DelegationCreated"]
  E8 --> P5["POL: Re-route open items to delegate; forbid re-delegation"]

  C2 -.-> ERR1["ERR: approver lacks authority (ABAC check) -> 403, decision not recorded"]
  P3 -.-> ERR2["ERR: grant provisioning fails -> approval stays Granted-Pending, retry with backoff, ops alert after 3 fails"]
  T3["POL: request expiry (window passed)"] --> E9["EVT: ApprovalExpired"]
  E9 --> X3["EXT: Notify requester to re-submit"]
```

## 3.4 Physical Access Validation flow

```mermaid
flowchart LR
  X1["EXT: Reader (RFID/QR presentation)"] --> C1["CMD: ValidateAccess (edge gateway)"]
  C1 --> P1["POL: Decision pipeline: credential -> cardholder -> grant -> schedule -> ABAC -> anti-passback -> capacity"]
  P1 --> E1["EVT: AccessDecisionRecorded (Permit)"]
  P1 --> E2["EVT: AccessDecisionRecorded (Deny + reason code)"]
  E1 --> X2["EXT: Door controller releases lock"]
  E1 --> P2["POL: Update zone occupancy"]
  P2 --> E3["EVT: ZoneOccupancyChanged"]
  E3 --> RM1["RM: real-time occupancy board"]
  E1 --> RM2["RM: append-only decision log"]
  E2 --> RM2

  E2 --> P3["POL: 3 denies at one reader in 5 min -> alarm"]
  P3 --> E4["EVT: SecurityAlarmRaised"]
  E4 --> X3["EXT: SOC dashboard + Sentinel"]

  C1 -.-> ERR1["ERR: cloud unreachable -> offline mode: validate against local snapshot (max staleness 24h)"]
  ERR1 --> E5["EVT: AccessDecisionRecorded (offline=true), queued locally"]
  E5 --> P4["POL: On reconnect: upload queued decisions, reconcile against revocations since last sync"]
  P4 --> E6["EVT: OfflineDecisionConflictFlagged (badge revoked after last sync but permitted offline)"]
  E6 --> X3
  P1 -.-> ERR2["ERR: snapshot staleness beyond limit -> fail-secure deny (configurable per zone criticality)"]
```

**Failure/compensation:** offline validation is a designed degradation, not an error —
decisions queue and reconcile on reconnect, with conflicts (revoked-but-permitted) flagged
to the SOC; snapshot beyond max staleness fails secure on restricted zones and fail-open
is an explicit per-zone life-safety configuration (never default).

<!-- SECTION 3 COMPLETE -->
