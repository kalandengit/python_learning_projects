# MASTER_PROMPT — Enterprise AMS Architecture Generator v6.0 (record of requirements)

This file records the governing requirements the architecture package in
`docs/architecture/` was generated against. It is the traceability anchor for the
acceptance checklist in `docs/architecture/appendix-acceptance-checklist.md`.

## Governing constraints (v6.0)

- **Stack:** .NET 10 LTS / C# 14 · PostgreSQL 18 (`uuidv7()`, async I/O) · React 19 + MUI v7 ·
  Redis 7.x · Azure Event Hubs (Kafka) · AKS 1.30+ · Terraform + ArgoCD GitOps ·
  OpenTelemetry / Prometheus / Grafana / Loki / Tempo.
- **Platform:** Azure — West Europe primary, North Europe secondary (active-active DR).
  Only the services listed in the prompt's platform table; additions require an ADR.
- **Scale targets:** 500 sites · 100,000 employees · 250,000 cardholders · 25,000 visitors/day
  (current: 20 sites · 5,000 employees · 15,000 credentials · 1,000 visitors/day).
- **Compliance:** ISO 27001 · SOC 2 Type II · GDPR · NIST CSF 2.0 (incl. Govern).
  Every security control maps to all four frameworks.
- **Performance:** badge validation P95 < 200 ms / P99 < 400 ms · API P95 < 200 ms / P99 < 600 ms ·
  auth P95 < 300 ms / P99 < 500 ms · approvals P95 < 2 h / P99 < 4 h · availability 99.95 %
  (99.99 % critical paths). Every target must reappear in Section 13 as an SLO with an
  error budget and a multi-window burn-rate alert.
- **Event Sourcing discipline:** ES only where immutable, replayable history is a genuine
  requirement (Audit, Badge lifecycle). All other contexts: CRUD + transactional outbox +
  append-only audit projection, with a per-context verdict in Section 2.
- **Anti-hallucination:** state-or-omit rule; no fabricated citations, CVEs, clause IDs or
  SKUs; per-code-block `// VERIFY:` self-check; version honesty ("verify latest patch").
- **ADR honesty:** every ADR (Sections 5 and 15) carries a mandatory
  **"When this is the wrong choice"** clause.
- **Optional seams only:** AI/ML anomaly detection and blockchain-anchored audit are
  deferred — interface + event contract + deferral ADR, no core budget spent.
- **Output:** 16 numbered sections, each ending with `<!-- SECTION N COMPLETE -->`;
  no placeholders ("TODO"/"TBD"/"..."); Mermaid-valid diagrams; language-tagged code blocks;
  acceptance-test harness self-audit appended.

## Required deliverables

1. Product Requirements Document (≥ 6 personas, 3–5 OKRs, ≥ 10 KPIs, ≥ 50 FRs, ≥ 20 NFRs,
   Given/When/Then for top 15 FRs, constraints vs assumptions)
2. Domain-Driven Design (≥ 8 bounded contexts, per-context CRUD-vs-ES verdict, context map)
3. Event Storming (4 flows, failure/compensation paths)
4. C4 Architecture (L1–L4, Mermaid)
5. ≥ 20 ADRs
6. ≥ 10 microservices + dependency/data-ownership matrix
7. Database architecture (PG 18 DDL, uuidv7 PKs, partitioning, RPO/RTO, event store/outbox/WORM)
8. Security architecture (Zero Trust, RBAC/ABAC, STRIDE + residual risk, compliance map)
9. OpenAPI 3.1, ≥ 20 endpoints (RFC 7807, cursor pagination, Idempotency-Key, webhooks)
10. Workflow architecture (5 flows, state + sequence, error paths, offline-edge fallback)
11. UX architecture (≥ 25 screens, SecOps dashboard, MUI v7 tokens, WCAG 2.2 AA plan)
12. DevOps (CI/CD YAML, GitOps, Terraform, Helm, Blue/Green + Canary, DORA targets)
13. Observability (metrics catalog, log schema + PII masking, traces, dashboards,
    Prometheus rules, SLO/error-budget/burn-rate per service)
14. Scalability (capacity model with shown arithmetic, multi-region active-active,
    cache invalidation + stampede protection, performance budgets)
15. ≥ 11 technology ADRs (incl. .NET 10 vs 9 and PostgreSQL 18 vs 16 version ADRs)
16. Delivery plan (team topology, roadmap, Gantt, RACI, RAID, risk register, staffing,
    budget categories, Definition of Done)

## Required code artefacts (each ends with `// VERIFY:`)

Aggregate root (C#) · domain events (C#) · MediatR handler with FluentValidation +
structured logging (C#) · Minimal API endpoint with RFC 7807 + Idempotency-Key (C#) ·
repository interface + PostgreSQL implementation (C#) · outbox publisher background
service (C#) · Event Hubs producer (C#) · Terraform modules (AKS/PostgreSQL/Redis) ·
Helm chart · full GitHub Actions CI/CD.
