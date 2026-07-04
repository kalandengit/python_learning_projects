# Section 6 — Microservices Architecture (10 services)

Common properties (all services): .NET 10 Minimal APIs · hexagonal layout per Section 4.5 ·
OAuth2 client-credentials or user JWT via APIM · OTel instrumented · transactional outbox
(ADR-019) · DB-per-service (PostgreSQL 18 database + role per service) · HPA-driven scaling ·
liveness/readiness/startup probes · REST versioned `/v1/...`.

## 6.1 Service catalog

### 1. identity-service (Identity & Cardholder context)
- **Responsibility:** Mirror workforce identity from Entra ID/HR; own cardholder lifecycle & attributes.
- **Endpoints:** `GET/POST /v1/cardholders`, `GET/PATCH /v1/cardholders/{id}`, `POST /v1/cardholders/{id}/suspend`, `GET /v1/cardholders/{id}/credentials`, `POST /v1/imports/cardholders` (bulk).
- **Publishes:** `cardholder.onboarded|suspended|offboarded`, `contract.window-changed`, `clearance.changed`.
- **Consumes:** Entra provisioning events (Graph change notifications via ingest adapter).
- **Owns DB:** `ams_identity` (cardholders, contracts, trainings, sync-state).
- **SLOs:** availability 99.95 %; read P95 < 150 ms; Entra-disable → suspension ≤ 60 s P99.
- **Scaling:** HPA on CPU (70 %) + sync-lag metric; baseline 3 replicas/region.

### 2. visitor-service (Visitor context)
- **Responsibility:** Visits, pre-registration, screening, check-in/out, overstay handling.
- **Endpoints:** `POST/GET /v1/visitors`, `GET/PATCH /v1/visitors/{id}`, `POST /v1/visits/{id}/check-in`, `POST /v1/visits/{id}/check-out`, `POST /v1/visits/{id}/cancel`, group-visit variants.
- **Publishes:** `visit.registered|approved|cancelled`, `check-in.completed`, `check-out.completed`, `visit.overstayed`, `screening.hit`.
- **Consumes:** `approval.granted|rejected`, `badge.issued|revoked`, `cardholder.*`.
- **Owns DB:** `ams_visitor` (visits, documents, watchlist, screening results).
- **SLOs:** availability 99.95 %; check-in API P95 < 200 ms; host-notify hand-off ≤ 2 s.
- **Scaling:** HPA on RPS per pod (target 100) — arrival peaks are spiky; baseline 3/region.

### 3. badge-service (Badge context — event-sourced) — *reference implementation in `src/`*
- **Responsibility:** Badge lifecycle state machine, credential material, QR signing, validation snapshots.
- **Endpoints:** `POST/GET /v1/badges`, `GET /v1/badges/{id}`, `POST /v1/badges/{id}/activate|suspend|revoke|replace`, `POST /v1/badges/{id}/report-lost`.
- **Publishes:** `badge.requested|issued|activated|suspended|revoked|replaced|expired`.
- **Consumes:** `check-in.completed` (issue visitor badge), `cardholder.suspended|offboarded`, `contract.window-changed`, `visit.*` (auto-expiry).
- **Owns DB:** `ams_badge` (append-only `badge_events` stream + `badge_current_state`, `credential_snapshot` read models).
- **SLOs:** availability 99.99 % (feeds the critical path); issue P95 < 250 ms; revocation event publish ≤ 1 s P99.
- **Scaling:** HPA on outbox lag + CPU; projections scale by Event Hubs partition count; baseline 3/region.

### 4. access-control-service (Access Control context)
- **Responsibility:** Policies, grants, the validation decision pipeline, anti-passback, decision log.
- **Endpoints:** `POST /v1/badge-validations` (+ internal gRPC `Validate`), `POST/GET /v1/access-requests` (grant provisioning side), `GET /v1/grants`, `POST /v1/policies` (versioned publish), `GET /v1/decisions` (cursor-paged log).
- **Publishes:** `access.granted|revoked`, `policy.published`, `decision.recorded`, `alarm.raised`.
- **Consumes:** `badge.*` (snapshot updates), `cardholder.*`, `approval.granted`, `site.config-published`.
- **Owns DB:** `ams_access` (policies, grants, partitioned `access_decisions` append-only log).
- **SLOs:** availability 99.99 %; validation P95 < 200 ms / P99 < 400 ms server-side; revocation-to-cache ≤ 5 s P99.
- **Scaling:** HPA on P95 latency + RPS (KEDA on Event Hubs lag for consumers); baseline 4/region — the hottest service.

### 5. approval-service (Approval context)
- **Responsibility:** Approval chains, SLA escalation timers, delegation.
- **Endpoints:** `POST/GET /v1/access-requests`, `GET /v1/access-requests/{id}`, `POST .../approve|reject|delegate`, `GET /v1/delegations`, `POST /v1/delegations`.
- **Publishes:** `approval.requested|stage-completed|escalated|granted|rejected|expired`, `delegation.created|revoked`.
- **Consumes:** `visit.registered` (visit approval), `cardholder.*` (approver validity).
- **Owns DB:** `ams_approval` (requests, stages, delegations, durable timers).
- **SLOs:** availability 99.95 %; decision API P95 < 200 ms; escalation timer accuracy ± 60 s.
- **Scaling:** HPA on CPU; timer worker singleton-per-partition via lease; baseline 2/region.

### 6. notification-service (Notification context)
- **Responsibility:** Multi-channel delivery (email/push/Teams/SMS), templates, preferences, retry.
- **Endpoints:** `POST /v1/notifications` (internal), `GET /v1/notifications/{id}`, `GET/PUT /v1/preferences/{principal}`.
- **Publishes:** `notification.delivered|failed`.
- **Consumes:** `check-in.completed`, `approval.*`, `badge.*`, `visit.*`, `alarm.raised`, `evacuation.*`.
- **Owns DB:** `ams_notification` (requests, attempts, templates, preferences) — 30-day retention.
- **SLOs:** availability 99.9 %; enqueue-to-first-attempt ≤ 5 s P95 (host notify budget: 10 s end-to-end).
- **Scaling:** KEDA on Event Hubs consumer lag; baseline 2/region.

### 7. audit-service (Audit & Compliance context — append-only)
- **Responsibility:** Normalise every integration event into audit envelopes; WORM replication; evidence queries; retention/pseudonymisation jobs.
- **Endpoints:** `GET /v1/audit-events` (cursor-paged, ABAC-filtered), `POST /v1/evidence-queries`, `GET /v1/evidence-queries/{id}` (async results), `POST /v1/erasure-requests`.
- **Publishes:** `audit.appended` (internal watermark), `erasure.completed`.
- **Consumes:** **all** integration events (dedicated consumer group).
- **Owns DB:** `ams_audit` (partitioned append-only `audit_events`; INSERT-only role) + WORM blob container.
- **SLOs:** availability 99.95 %; ingestion lag ≤ 60 s P99; evidence query ≤ 15 min for 12-month windows.
- **Scaling:** KEDA on consumer lag; partition-parallel writers; baseline 3/region.

### 8. site-service (Site & Topology context)
- **Responsibility:** Sites/buildings/zones, device registry, edge config-snapshot compilation & signing.
- **Endpoints:** `GET/POST /v1/sites`, `GET /v1/sites/{id}`, `GET/POST /v1/sites/{id}/zones`, `POST /v1/devices`, `POST /v1/sites/{id}/config-snapshots`, `GET /v1/devices/{id}/health`.
- **Publishes:** `site.onboarded`, `zone.defined`, `device.registered|offline`, `site.config-published`.
- **Consumes:** `badge.*`, `access.granted|revoked`, `policy.published` (snapshot inputs).
- **Owns DB:** `ams_site` (topology, devices, snapshot versions).
- **SLOs:** availability 99.95 %; snapshot compile ≤ 30 s per site P95.
- **Scaling:** HPA on CPU; snapshot compiler as queue-driven worker; baseline 2/region.

### 9. occupancy-service (Occupancy & Evacuation — subdomain of Access, separate for life-safety isolation)
- **Responsibility:** Real-time occupancy projection, capacity rules feed, evacuation/muster orchestration, warden sync.
- **Endpoints:** `GET /v1/sites/{id}/occupancy`, `GET /v1/zones/{id}/occupancy`, `POST /v1/sites/{id}/evacuations`, `POST /v1/evacuations/{id}/persons/{pid}/mark-safe`, `GET /v1/evacuations/{id}/muster-report`.
- **Publishes:** `occupancy.changed`, `evacuation.activated|completed`, `muster.person-status-changed`.
- **Consumes:** `decision.recorded` (entry/exit), `check-in/out.completed`.
- **Owns DB:** `ams_occupancy` (projection tables, evacuation runs, muster marks).
- **SLOs:** availability 99.99 % during evacuation mode; occupancy lag ≤ 5 s P95; muster list ≤ 30 s.
- **Scaling:** KEDA on decision-event lag; WebSocket/SSE fan-out via Redis pub/sub; baseline 2/region.

### 10. reporting-service (Compliance Reporting — read-only over projections)
- **Responsibility:** Scheduled/on-demand compliance packs, access-review campaigns, KPI exports.
- **Endpoints:** `POST /v1/reports` (async), `GET /v1/reports/{id}`, `GET /v1/report-definitions`, `POST /v1/access-reviews`, `POST /v1/access-reviews/{id}/attest`.
- **Publishes:** `report.completed`, `access-review.completed`, `grant.revocation-requested` (non-attested grants).
- **Consumes:** `audit.appended` watermarks, `access.granted|revoked`.
- **Owns DB:** `ams_reporting` (denormalised marts, campaign state) — rebuilt from audit/read models, never a source of record.
- **SLOs:** availability 99.9 %; scheduled pack on time 99.5 %.
- **Scaling:** queue-driven workers, scale-to-1 off-peak (FinOps); baseline 1/region.

## 6.2 Dependency & data-ownership matrix

Legend: **O** = owns database (sole writer) · **E→** publishes event · **→E** consumes event · **S** = synchronous call (must stay rare).

| Service | ams_identity | ams_visitor | ams_badge | ams_access | ams_approval | ams_notification | ams_audit | ams_site | ams_occupancy | ams_reporting | Sync deps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | **O** | | | | | | | | | | Entra Graph (S) |
| visitor | →E | **O** | →E | | →E | | | →E | | | none |
| badge | →E | →E | **O** | | | | | →E | | | Key Vault sign (S) |
| access-control | →E | | →E | **O** | →E | | | →E | | | Redis snapshot (S) |
| approval | →E | →E | | | **O** | | | →E | | | none |
| notification | →E | →E | →E | →E | →E | **O** | | | →E | | Email/Teams providers (S) |
| audit | →E all | →E all | →E all | →E all | →E all | →E all | **O** | →E all | →E all | | WORM blob (S) |
| site | | | →E | →E | | | | **O** | | | none |
| occupancy | | →E | | →E | | | | →E | **O** | | Redis pub/sub (S) |
| reporting | →E | →E | →E | →E | →E | | →E | →E | →E | **O** | none |

**Coupling review:** every column has exactly one **O** — no shared databases. The only
synchronous cross-service dependencies are to *platform* services (Entra, Key Vault,
Redis, blob, mail), never service→service REST on the hot path; inter-service knowledge
flows through events. The validation hot path (access-control) depends only on its own DB
+ Redis snapshot, so badge/visitor outages degrade freshness, not availability
(EDA + Zero Trust "assume breach" blast-radius containment).

## 6.3 Event topics (Event Hubs)

| Hub (topic) | Partitions (prod) | Key | Producers → Consumers |
|---|---|---|---|
| `ams.cardholder` | 8 | cardholderId | identity → badge, access, visitor, approval, audit, reporting |
| `ams.visit` | 16 | visitId | visitor → badge, notification, occupancy, audit, reporting |
| `ams.badge` | 16 | badgeId | badge → access, visitor, notification, site, audit, reporting |
| `ams.access` | 32 | zoneId | access → occupancy, notification, site, audit, reporting |
| `ams.decision` | 32 | readerId | access → occupancy, audit, (seam: anomaly-detection) |
| `ams.approval` | 8 | requestId | approval → visitor, access, notification, audit, reporting |
| `ams.site` | 4 | siteId | site → access, audit, reporting |
| `ams.evacuation` | 4 | siteId | occupancy → notification, audit, reporting |

Partition counts are sized in Section 14.1 (peak ~150 decision TPS → 32 partitions keeps
per-partition throughput < 10 msg/s at 20× headroom).

<!-- SECTION 6 COMPLETE -->
