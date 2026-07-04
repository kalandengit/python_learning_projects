# Section 15 — Technology ADRs (11)

Same format as Section 5; all **Accepted**.

## ADR-T01 — React vs Angular
- **Context:** Three distinct UIs (operator SPA, kiosk, warden mobile web) sharing a design system; hiring pool; MUI v7 mandated.
- **Decision:** React 19 + TypeScript. Concurrent rendering suits live SOC feeds; MUI is React-native; largest hiring pool; one mental model across all three bundles.
- **Consequences:** Architectural discipline must come from us (lint rules, folder conventions) since React prescribes little; state kept in TanStack Query (server) + minimal local state.
- **When this is the wrong choice:** Teams already deep in Angular, or orgs wanting a batteries-included framework with enforced structure and DI — Angular's opinionation is a feature there.
- **Alternatives:** Angular (heavier, MUI mismatch), Vue/Svelte (smaller enterprise talent pools).

## ADR-T02 — .NET vs Java
- **Context:** Azure-first estate, Entra integration everywhere, high-perf minimal APIs, existing C# skills.
- **Decision:** .NET 10 / C# 14. First-class Azure SDKs and Entra auth, Minimal APIs + source generators give low-allocation hot paths, single vendor-aligned toolchain (ASP.NET Core, EF-free Npgsql data access, OTel support).
- **Consequences:** Windows-centric image bloat avoided via Linux containers; team standardises on one backend stack.
- **When this is the wrong choice:** JVM-centric organisations (existing Kafka/Spring platform teams, JVM observability estate) — Java 21 + Spring Boot 3 would match their operating muscle.
- **Alternatives:** Java/Spring (equally capable, worse Azure ergonomics here), Go (great for edge gateway — kept as an option for that component only), Node (weaker for CPU-bound decision pipeline).

## ADR-T03 — PostgreSQL vs SQL Server
- **Context:** DB-per-service, JSONB event/audit payloads, partitioning, licence cost at 10 databases × 4 envs × 2 regions.
- **Decision:** PostgreSQL 18 Flexible Server. Native JSONB + GIN, declarative range partitioning, `uuidv7()`, no per-core licensing, open ecosystem (pgBouncer etc.).
- **Consequences:** Team learns PG operational idioms (vacuum, bloat, partition maintenance) — platform runbooks cover this.
- **When this is the wrong choice:** Estates with deep SQL Server investment (SSRS/SSIS, DBA guild, EA licensing already sunk) or hard requirements on SQL Server-only features.
- **Alternatives:** SQL Server (licence + JSONB story), Cosmos DB (wrong consistency/cost profile for relational core).

## ADR-T04 — Redis vs Memcached
- **Context:** Needs beyond caching: idempotency store, pub/sub fan-out, distributed locks, sorted sets for anti-passback, streams.
- **Decision:** Redis 7.x (Azure Cache, zone-redundant). One engine covers cache + coordination primitives; Memcached covers only plain KV.
- **Consequences:** Must resist "Redis as a database" scope creep — rule: everything in Redis must be rebuildable (Section 7.5).
- **When this is the wrong choice:** Pure ephemeral KV cache at extreme scale with multi-threaded throughput as the only criterion — Memcached is simpler and faster per core there.
- **Alternatives:** Memcached (insufficient primitives), in-process caches only (no cross-pod coherence).

## ADR-T05 — Event Hubs vs RabbitMQ
- **Context:** Ordered, replayable, partitioned event log consumed by 5+ independent groups; audit ingestion must be able to re-read.
- **Decision:** Azure Event Hubs (Kafka protocol). Log semantics (offset replay, consumer groups, capture-to-blob) match the audit/projection architecture; fully managed.
- **Consequences:** No per-message TTL/dead-letter (mitigated by inbox pattern and poison-event parking tables); partition-count planning up front.
- **When this is the wrong choice:** Complex routing topologies, per-message acknowledgement/dead-lettering, priority queues → broker semantics (RabbitMQ / Service Bus) win.
- **Alternatives:** RabbitMQ (queue, not log), self-managed Kafka (ops), Service Bus (log semantics absent).

## ADR-T06 — AKS vs Azure Container Apps
- **Context:** Service mesh mTLS, Flagger canaries, network policies, KEDA, ArgoCD, gRPC — and a funded platform team.
- **Decision:** AKS. Full Kubernetes API needed for the mesh/canary/GitOps stack; multi-region cluster symmetry; node-pool control for cost tiers.
- **Consequences:** We own upgrade cadence, node images, capacity — platform team staffed for it (Section 16).
- **When this is the wrong choice:** No dedicated platform team, or workloads that are plain HTTP microservices — Container Apps (built on the same tech) removes 80 % of the ops for 80 % of the features.
- **Alternatives:** Container Apps (insufficient control), App Service (no mesh), Functions-only (unsuitable for long-running consumers).

## ADR-T07 — Terraform vs Bicep
- **Context:** IaC for Azure + GitHub + Grafana + Kubernetes providers; team may support non-Azure SaaS resources.
- **Decision:** Terraform (AzureRM). One language across all providers, mature module ecosystem, plan-based review culture, state-driven drift detection.
- **Consequences:** State management is ours (remote state, locking, access control); AzureRM occasionally lags new Azure features (escape hatch: `azapi` provider).
- **When this is the wrong choice:** Pure-Azure shop wanting zero state management and day-0 API coverage — Bicep is the honest pick.
- **Alternatives:** Bicep (Azure-only), Pulumi (imperative temptation, smaller reviewer pool).

## ADR-T08 — OpenTelemetry vs proprietary APM
- **Context:** Multi-backend telemetry (Prometheus/Grafana/Loki/Tempo + Azure Monitor/Sentinel), 10 services, no vendor lock on instrumentation.
- **Decision:** OTel SDK + Collector everywhere; exporters fan out to both stacks. Instrumentation is written once, backends are swappable config.
- **Consequences:** Collector becomes tier-1 infrastructure (HA daemonset + gateway pair); some APM conveniences (auto code-level profiling) need explicit setup.
- **When this is the wrong choice:** Small team all-in on one APM vendor whose agent gives instant value — the collector indirection would be pure overhead.
- **Alternatives:** App Insights SDK only (lock-in), Datadog/Dynatrace agents (cost + lock-in, not in the platform service list).

## ADR-T09 — GitHub Actions vs Azure DevOps
- **Context:** Code is on GitHub; OIDC federation to Azure; environments/required-reviewer gates; CodeQL native.
- **Decision:** GitHub Actions for CI and CD orchestration (with ArgoCD doing the actual delivery). Single platform for code, reviews, checks, security scanning, and pipeline — fewer identities and integration seams (supply-chain surface, Section 8.5).
- **Consequences:** Self-hosted runners needed for network-restricted jobs (e.g., Terraform against private endpoints); Azure Boards features not included (planning stays in the existing PPM tool).
- **When this is the wrong choice:** Organisations living in Azure DevOps repos/boards with mature classic pipelines — migration cost outweighs consolidation benefit.
- **Alternatives:** Azure DevOps (split-brain with GitHub code), GitLab (platform migration out of scope).

## ADR-T10 — .NET 10 (LTS) vs .NET 9 (version ADR)
- **Context:** Greenfield multi-year platform starting 2026; .NET 9 is an STS release whose support ends **10 November 2026** — within months of our first production sites. An architecture review board rightly rejects building new regulated-industry systems on a runtime that EOLs mid-rollout.
- **Decision:** .NET 10 LTS / C# 14 — supported ~3 years (to Nov 2028), giving the whole 30-month rollout one supported runtime, with the .NET 12 LTS upgrade planned as routine lifecycle work (*verify exact end-of-support dates against the published .NET support policy*).
- **Consequences:** Newest-major dependency risk (early-cycle package compatibility) accepted; pinned SDK via `global.json` and quarterly patch cadence.
- **When this is the wrong choice:** Short-lived experiments or teams needing a runtime already battle-tested for a year — shipping an STS (or the previous LTS, .NET 8, before *its* EOL) can be rational there.
- **Alternatives:** .NET 9 (EOL 10 Nov 2026 — disqualifying), .NET 8 LTS (loses C# 13/14 features and ends support earlier in our rollout than .NET 10).

## ADR-T11 — PostgreSQL 18 vs 16 (version ADR)
- **Context:** This system is dominated by high-write, time-ordered tables (decisions, audit, badge events). PG 18 ships native `uuidv7()` and an asynchronous I/O subsystem; PG 16 has neither and is ~2 years closer to end of community support.
- **Decision:** PostgreSQL 18. (1) **Native `uuidv7()`**: time-ordered PKs in-engine — no extension to certify — giving right-edge B-tree inserts on exactly our hottest tables (Section 7.1) and stable keyset cursors (ADR-018). (2) **Async I/O**: improved read throughput benefits sequential scans of audit/event partitions (evidence queries, projections) (*verify workload benefit with our own benchmarks; gains are workload-dependent*). (3) **Support runway**: ~5-year community window covers rollout + steady state without a forced major upgrade mid-programme.
- **Consequences:** Newer major on a managed platform — confirm regional availability of the PG 18 tier at provisioning time (*illustrative assumption in Terraform: version pinned as a variable, one-line change*); ecosystem tooling (pgBouncer, logical-replication consumers) verified against 18 in the platform test env.
- **When this is the wrong choice:** If Flexible Server PG 18 were unavailable in West/North Europe at build time, we would start on the newest available major with `pg_uuidv7` extension and a planned in-place major upgrade — the schema is written to be version-portable.
- **Alternatives:** PG 16 (no uuidv7/async-I/O; earlier EOL forces an upgrade during peak rollout), PG 17 (halfway house; still lacks native uuidv7).

<!-- SECTION 15 COMPLETE -->
