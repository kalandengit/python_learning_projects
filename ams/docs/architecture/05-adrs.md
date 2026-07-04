# Section 5 — Architecture Decision Records (20)

Format per ADR: Status · Context · Decision · Consequences · **When this is the wrong
choice** · Alternatives considered. All are **Accepted** unless noted.

---

## ADR-001 — Microservices aligned to bounded contexts

- **Context:** 10 product capabilities, multiple teams, independent scaling needs (badge
  validation at 150+ TPS vs. reporting at near-zero), 500-site rollout over 30 months.
- **Decision:** One deployable service per bounded context (Section 2), strict DB-per-service,
  async integration via Event Hubs. Principles: DDD, EDA, 12-Factor.
- **Consequences:** Independent deploys and scaling; per-service SLOs; distributed-system
  costs (eventual consistency, tracing, contract management) accepted and mitigated by
  outbox + OTel + schema registry conventions.
- **When this is the wrong choice:** A single team or < ~5 engineers, or an MVP whose scale
  fits one Postgres and one process — then a modular monolith with the same internal
  boundaries ships months faster. Also wrong if the org can't fund platform engineering.
- **Alternatives:** Modular monolith (kept as the explicit fallback shape — contexts are
  assemblies first, services second); serverless-per-function (rejected: cold-start on the
  validation path, weaker local dev story).

## ADR-002 — CQRS with MediatR, without event-sourcing-everything

- **Context:** Read patterns (dashboards, edge snapshots) differ radically from writes.
- **Decision:** Command/query separation in every service via MediatR pipeline (validation,
  logging, idempotency behaviors); read models as projected tables/Redis structures.
  Event Sourcing only per ADR-003.
- **Consequences:** Testable use cases, uniform cross-cutting behaviors; some indirection
  overhead; MediatR license moved to commercial for newer majors — pin the OSS-licensed
  version in use or budget the license (*verify current licensing before upgrade*).
- **When this is the wrong choice:** CRUD-only admin services with three endpoints — a
  plain handler class is simpler; don't cargo-cult the pipeline where there's no pipeline
  behavior to share.
- **Alternatives:** Hand-rolled dispatcher (viable, more code); Wolverine (attractive,
  smaller talent pool).

## ADR-003 — Event Sourcing ONLY for Badge and Audit contexts

- **Context:** Master requirement: immutable, replayable history where it is a genuine
  requirement; ES system-wide is an anti-pattern (complexity tax on every context).
- **Decision:** Badge lifecycle and Audit are event-sourced/append-only; Visitor, Approval,
  Site, Identity, Notification, Access-policy use CRUD + transactional outbox + audit
  projection. Access *decisions* are an append-only log (immutable facts) without
  aggregate replay.
- **Consequences:** Compliance-grade history exactly where auditors demand it; the other
  six contexts keep simple queries, easy GDPR erasure, and junior-friendly code.
- **When this is the wrong choice:** If regulators later demand replayable history of
  *approvals* (not just their audit trail), Approval would migrate to ES — the outbox
  events already capture the needed data to backfill a stream.
- **Alternatives:** ES everywhere (rejected — see context); temporal tables (weaker: no
  intent, only state diffs); CDC/Debezium as history (operationally heavy on Azure).

## ADR-004 — Redis for cache, idempotency, and hot validation state

- **Context:** Badge validation must hit < 200 ms P95 including policy evaluation; API
  reads dominate writes ~20:1; idempotency keys need fast TTL storage.
- **Decision:** Azure Cache for Redis (zone-redundant tier) for: credential/policy
  snapshot cache, API response cache, Idempotency-Key store (24 h TTL), anti-passback
  state, pub/sub for dashboard fan-out.
- **Consequences:** Sub-ms reads on the hot path; one more stateful dependency — mitigated
  by cache-miss-tolerant design (DB fallback, stampede protection per Section 14.5).
- **When this is the wrong choice:** If the working set were tiny and per-pod, in-process
  caching (`IMemoryCache`) suffices; Redis as a *primary* store of record is always wrong
  here.
- **Alternatives:** Memcached (no persistence/streams/pubsub — see ADR-T04); Cosmos DB as
  cache (cost, latency variance).

## ADR-005 — Azure Event Hubs (Kafka protocol) as the event backbone

- **Context:** Ordered, partitioned, replayable event distribution to many consumers
  (projections, audit, edge sync, SIEM) at six-figure daily event volume.
- **Decision:** Event Hubs Premium with Kafka API, partition key = aggregate ID (ordering
  per aggregate), consumer groups per service, capture-to-blob for replay/DR.
- **Consequences:** Kafka semantics without cluster ops; per-partition ordering only —
  cross-aggregate ordering must never be assumed (enforced in consumer design).
- **When this is the wrong choice:** Point-to-point commands with per-message TTL, dead-letter
  and sessions → Azure Service Bus is the right tool (used for notification dispatch if
  queue semantics are needed; would require an ADR update to add the service).
- **Alternatives:** Self-managed Kafka on AKS (ops burden), Service Bus (no replay/compaction
  semantics needed here), Redis Streams (fine intra-service, not as the enterprise backbone).

## ADR-006 — PostgreSQL 18 Flexible Server as the OLTP standard

- **Context:** Relational integrity, JSONB flexibility, partitioning for high-volume
  decision/audit tables, EU-region managed service.
- **Decision:** One Flexible Server per region/environment; database-and-role per service;
  `uuidv7()` primary keys; monthly range partitions on event/decision/audit tables; zone-redundant
  HA + geo read replica.
- **Consequences:** Single engine to master; time-ordered PKs give B-tree locality (see
  ADR-T10/T11); per-service databases keep the DB-per-service rule cheap to operate.
- **When this is the wrong choice:** Genuinely global multi-master writes with regional
  write latency requirements → a distributed SQL engine; heavy graph traversal workloads.
- **Alternatives:** SQL Server (ADR-T03), Cosmos DB (consistency/cost trade-offs wrong for
  relational core).

## ADR-007 — OpenTelemetry end-to-end

- **Context:** NFR-018/019: traces, metrics, logs across HTTP, gRPC and Event Hubs hops.
- **Decision:** OTel SDK auto+manual instrumentation in every service; W3C tracecontext
  propagated in event headers; OTel Collector daemonset → Prometheus/Loki/Tempo + Azure
  Monitor exporter.
- **Consequences:** Vendor-neutral telemetry (ADR-T08); collector is a critical component
  with its own SLO.
- **When this is the wrong choice:** A two-service system fully on App Insights SDK with no
  multi-backend need — the collector layer would be ceremony.
- **Alternatives:** App Insights SDK only (lock-in, weaker Kafka propagation story).

## ADR-008 — API versioning via URL path (`/v1/...`)

- **Context:** External integrators (edge gateways, partner systems) need unambiguous,
  cache-friendly versioning.
- **Decision:** Major version in path; additive changes within a major; breaking changes
  = new major, old major supported ≥ 12 months; deprecation via `Sunset` header.
- **Consequences:** Simple routing/caching at APIM/Front Door; URL churn on majors —
  acceptable because majors are rare by policy.
- **When this is the wrong choice:** Content-negotiation versioning suits hypermedia APIs
  with sophisticated clients; header versioning suits internal-only APIs where URLs must
  stay stable.
- **Alternatives:** Header/media-type versioning; query-param versioning (poor cacheability).

## ADR-009 — Azure as the platform

- **Context:** Constraint C1 (EU residency), Entra ID as IdP, enterprise agreement in place.
- **Decision:** Azure, West Europe primary, North Europe secondary, active-active per
  Section 14.3; services restricted to the prompt's platform table.
- **Consequences:** Deep Entra/Sentinel/Defender integration; concentration risk accepted
  and mitigated by containerised workloads + Terraform (portable shape).
- **When this is the wrong choice:** Multi-cloud regulatory mandates, or an estate already
  standardised on another hyperscaler.
- **Alternatives:** AWS/GCP (no Entra-native Conditional Access story for this workforce).

## ADR-010 — AKS for workloads; Functions only for event-glue

- **Context:** Long-running consumers, gRPC, sidecar/mesh needs, GPU-free general compute.
- **Decision:** AKS 1.30+ (managed), system/user node-pool split, cluster autoscaler +
  HPA/KEDA; Azure Functions only for narrow event-handler glue (e.g., blob-capture
  post-processing). See ADR-T06 for AKS vs Container Apps.
- **Consequences:** Full k8s control (network policy, Flagger canaries, ArgoCD); platform
  team must own upgrades — staffed in Section 16.
- **When this is the wrong choice:** No platform team → Azure Container Apps trades control
  for operability and would be the honest choice.
- **Alternatives:** Container Apps (ADR-T06), App Service (no mesh/canary story).

## ADR-011 — Terraform (AzureRM) for IaC

- **Context:** Multi-environment, reviewable, drift-detectable infrastructure.
- **Decision:** Terraform with remote state (Azure Storage + state locking), reusable
  modules (`infra/terraform/modules`), plan-on-PR / apply-on-merge via CI with manual
  prod gate. See ADR-T07 vs Bicep.
- **Consequences:** Multi-cloud-portable skills; HCL module discipline required; state is
  a crown jewel (encrypted, access-controlled, backed up).
- **When this is the wrong choice:** Azure-only shop with zero Terraform skills and heavy
  ARM template estate → Bicep is defensible.
- **Alternatives:** Bicep, Pulumi (general-purpose languages tempt logic into infra).

## ADR-012 — GitOps with ArgoCD

- **Context:** 10+ services × 4 environments × 2 regions; drift must be impossible to hide.
- **Decision:** ArgoCD app-of-apps; desired state in a dedicated `ams-gitops` repo;
  CI pushes image tags via PR to that repo; humans never `kubectl apply` to prod.
- **Consequences:** Auditable deploy history = git log (compliance win); rollback = git
  revert; secrets stay in Key Vault via CSI driver, never in git.
- **When this is the wrong choice:** Single service, single env — push-based CD from CI is
  simpler and adequate.
- **Alternatives:** Flux (equally capable; ArgoCD UI aids SOC/auditor walkthroughs),
  push-based Helm from CI (no drift detection).

## ADR-013 — Deliberately tiny shared kernel

- **Context:** Shared libraries between services rot into a distributed monolith.
- **Decision:** `Ams.BuildingBlocks` contains only: strongly-typed ID base, aggregate/event
  base types, event-envelope headers, outbox message shape, idempotency middleware.
  No domain types, no shared DTOs. Contracts are duplicated per consumer (published
  language), not shared as binaries.
- **Consequences:** Services evolve independently; some duplication accepted as the price
  of autonomy (DRY applies within a context, not across contexts).
- **When this is the wrong choice:** A single-team codebase where the "kernel" and the
  services deploy together anyway.
- **Alternatives:** Shared contracts NuGet (version-lockstep hell), no shared code at all
  (idempotency/envelope drift).

## ADR-014 — Event versioning: additive-only + upcasters

- **Context:** Event-sourced streams live for years; consumers deploy independently.
- **Decision:** Event payloads are JSON with `eventType` + `schemaVersion` headers.
  Within a version: additive optional fields only. Breaking change: new event type
  (`BadgeIssued.v2`) + upcaster in consumers; producers dual-write during migration
  windows. No event is ever mutated or deleted.
- **Consequences:** Replays always work; upcaster code accumulates — scheduled compaction
  of read-model rebuild paths keeps it bounded.
- **When this is the wrong choice:** With a managed schema registry enforcing
  compatibility, registry-checked Avro/Protobuf could replace convention — revisit if
  contract drift ever causes an incident.
- **Alternatives:** Avro + registry (extra infra), weak-schema "tolerant reader" only
  (insufficient for 10-year audit streams).

## ADR-015 — Zero Trust enforcement layout (NIST SP 800-207)

- **Context:** Assume breach; the SOC must be able to answer "what enforced this decision?"
- **Decision:** Policy Engine = Entra ID Conditional Access (+ AMS ABAC for domain rules).
  PEPs: Front Door WAF (edge), APIM (token validation, rate limits), AKS network policies
  (default-deny), service-mesh mTLS (workload identity). Every human and workload
  authenticates per-request; no network location grants trust.
- **Consequences:** Multiple enforcement layers to keep consistent — codified in Terraform
  and policy-as-code tests; latency cost of per-hop authz kept in the Section-14 budget.
- **When this is the wrong choice:** Air-gapped OT networks where identity infrastructure
  is unreachable — there, compensating physical controls apply (documented per site).
- **Alternatives:** Perimeter model (fails FR/NFR and the threat model), third-party ZTNA
  overlay (duplicates Entra capabilities).

## ADR-016 — Frontend: React 19 SPA on Vite; no SSR/Next.js

- **Context:** All UIs sit behind authentication; SEO irrelevant; kiosk and SOC dashboards
  are long-lived sessions.
- **Decision:** SPA with React 19 + TypeScript 5 + Vite; TanStack Query v5 for server
  state; React Router 7; MUI v7 with design tokens; no Next.js.
- **Consequences:** Simple hosting (static + CDN via Front Door), no SSR server fleet to
  operate; initial-load budget enforced (Section 14.6) since there is no SSR to hide it.
- **When this is the wrong choice:** Public marketing/self-service pages needing SEO or
  sub-second first-paint on slow devices → add a Next.js edge for those routes only.
- **Alternatives:** Next.js 15 (SSR unjustified → this ADR is the required justification
  record), Angular (ADR-T01).

## ADR-017 — Idempotency-Key on all mutating endpoints

- **Context:** Kiosks and edge gateways retry aggressively on flaky links; duplicate badge
  issues or check-ins are a security defect, not a nuisance.
- **Decision:** `Idempotency-Key` (UUID) required on POST/PATCH; middleware stores
  key → response-hash in Redis (24 h TTL, per-principal scope); replay returns the
  original response with `Idempotency-Replayed: true`; mismatched payload for a seen key
  → RFC 7807 422.
- **Consequences:** At-least-once clients become effectively-once; Redis outage degrades
  to per-aggregate optimistic-concurrency protection (documented fallback).
- **When this is the wrong choice:** Naturally idempotent PUTs keyed by resource ID don't
  need it; don't force the header where the verb already guarantees safety.
- **Alternatives:** Deduplication only at aggregate level (weaker: can't replay the
  response), client-generated resource IDs everywhere (leaks ID minting to clients).

## ADR-018 — Cursor (keyset) pagination

- **Context:** Decision/audit tables reach billions of rows; `OFFSET` degrades linearly
  and skews under concurrent inserts.
- **Decision:** All collection endpoints use `page[size]`, `page[after]`, `page[before]`
  with opaque cursors encoding the keyset (uuidv7 PK is naturally time-ordered — the
  cursor is stable). Responses carry `links.next/prev`.
- **Consequences:** O(log n) pages at any depth; no "jump to page 37" — acceptable for
  operational UIs (search/filter replaces random access).
- **When this is the wrong choice:** Small bounded admin lists (< 1,000 rows) where users
  genuinely need numbered pages.
- **Alternatives:** Offset pagination (fails at scale), search-engine-backed pagination
  (adds infra for no current need).

## ADR-019 — Transactional Outbox for every event publisher

- **Context:** Dual-write (DB commit + broker publish) loses or duplicates events exactly
  when it hurts most.
- **Decision:** Every service writes state change + `outbox` row in one DB transaction;
  a background dispatcher publishes to Event Hubs with per-aggregate ordering and marks
  rows processed; consumers are idempotent (event ID dedupe). Delivery is at-least-once.
- **Consequences:** No lost events, no 2PC; small publish latency (dispatch interval
  ≤ 200 ms) and outbox-table hygiene (processed-row pruning job) to operate.
- **When this is the wrong choice:** Fire-and-forget telemetry where loss is acceptable —
  publish directly and skip the table.
- **Alternatives:** CDC/Debezium (heavier ops on Azure), Event Hubs transactions with DB
  (no atomic span across both exists).

## ADR-020 — Emergency evacuation: availability over consistency

- **Context:** During an evacuation, a slightly stale muster list that *renders* beats a
  perfectly consistent one that doesn't. Life-safety path.
- **Decision:** Occupancy/muster is an eventually-consistent projection updated from
  decision events; evacuation mode is activated site-locally (edge can trigger without
  cloud); warden mobile view works offline-first with CRDT-style safe-marking merge
  (last-writer-wins per person, "safe" wins ties); readers switch to muster-scan mode.
  Completeness is reconciled post-event and gaps are *explicitly displayed* ("14 unaccounted"),
  never hidden.
- **Consequences:** Muster list in ≤ 30 s even under partial outage; the report
  distinguishes "confirmed safe" from "no data", which drills must train wardens on.
- **When this is the wrong choice:** Sites with certified hard-gate mustering hardware
  (physical turnstile out-scan required) can run strict-consistency muster; the projection
  then only feeds dashboards.
- **Alternatives:** Synchronous muster ledger (fails exactly during the disaster it exists
  for); manual paper fallback (the status quo being replaced — retained as last-resort
  drill procedure).

<!-- SECTION 5 COMPLETE -->
