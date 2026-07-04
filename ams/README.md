# Enterprise Access Management System (AMS)

Production-grade, cloud-native architecture package and reference implementation for an
Enterprise Access Management System deployed across corporate offices, industrial
facilities, manufacturing plants, laboratories, warehouses, and data centres.

Generated against **MASTER_PROMPT v6.0** (see `docs/MASTER_PROMPT.md`).

## Stack

| Layer | Technology |
|---|---|
| Backend | .NET 10 (LTS) / C# 14, ASP.NET Core Minimal APIs, MediatR, FluentValidation, Mapperly |
| Persistence | PostgreSQL 18 (`uuidv7()` PKs, range partitioning), Redis 7.x, append-only event tables |
| Messaging | Azure Event Hubs (Kafka protocol), transactional outbox |
| Frontend | React 19 + TypeScript 5.x, Vite, TanStack Query v5, React Router 7, MUI v7 |
| Platform | Azure (West Europe primary / North Europe secondary), AKS 1.30+, Front Door, APIM |
| IaC / CD | Terraform (AzureRM), Helm, GitHub Actions, ArgoCD (GitOps) |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki, Tempo |

## Repository layout

```
ams/
├── docs/
│   ├── MASTER_PROMPT.md            # The v6.0 generator prompt (traceability)
│   └── architecture/               # The 16-section architecture package
│       ├── 00-index.md
│       ├── 01-prd.md               # Product Requirements Document
│       ├── 02-ddd.md               # Domain-Driven Design
│       ├── 03-event-storming.md
│       ├── 04-c4.md                # C4 diagrams L1–L4
│       ├── 05-adrs.md              # 20 Architecture Decision Records
│       ├── 06-microservices.md
│       ├── 07-database.md
│       ├── 08-security.md
│       ├── 09-api-design.md        # design rules; spec lives in api/openapi.yaml
│       ├── 10-workflows.md
│       ├── 11-ux.md
│       ├── 12-devops.md
│       ├── 13-observability.md
│       ├── 14-scalability.md
│       ├── 15-technology-adrs.md   # 11 technology ADRs
│       ├── 16-delivery-plan.md
│       └── appendix-acceptance-checklist.md
├── api/openapi.yaml                # OpenAPI 3.1, 26 operations, RFC 7807, webhooks
├── db/                             # PostgreSQL 18 production DDL
├── src/                            # .NET 10 solution (Badge service, reference impl)
├── frontend/                       # React 19 + MUI v7 scaffold
├── infra/terraform/                # AKS / PostgreSQL / Redis modules + prod env
├── deploy/helm/badge-service/      # Helm chart for a .NET service
├── observability/                  # Prometheus alert rules (SLO burn-rate)
└── .github/workflows → ../.github  # CI/CD pipelines live at repo root
```

> **Note on output format:** MASTER_PROMPT v6.0 asks for a single self-contained `.md`
> delivered in ordered chunks. In a git repository the equivalent — and more reviewable —
> shape is one file per numbered section under `docs/architecture/`, each ending with its
> `<!-- SECTION N COMPLETE -->` marker, plus `00-index.md` as the assembly order.
> Concatenating the files in index order reproduces the single document.

## Reference implementation scope

The **Badge service** is implemented end-to-end as the L4/C4 reference (hexagonal layout,
event-sourced aggregate, MediatR + FluentValidation, transactional outbox → Event Hubs,
RFC 7807 + Idempotency-Key Minimal API). The other nine services follow the identical
template and are specified in `docs/architecture/06-microservices.md`.

## Quick start (local)

```bash
# Backend (requires .NET 10 SDK, PostgreSQL 18, Redis)
cd src && dotnet build Ams.sln
psql -f ../db/001_badge_schema.sql -f ../db/002_partitioning.sql \
     -f ../db/003_outbox.sql -f ../db/004_audit_worm.sql
dotnet run --project Services/Badge/Ams.Badge.Api

# Frontend
cd frontend && npm install && npm run dev
```
