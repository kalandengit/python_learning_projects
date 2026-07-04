# AMS Enterprise Architecture Package — Index

Assembly order for the single-document view (concatenate in this order):

| # | File | Deliverable |
|---|------|-------------|
| 1 | `01-prd.md` | Product Requirements Document |
| 2 | `02-ddd.md` | Domain-Driven Design |
| 3 | `03-event-storming.md` | Event Storming (4 flows) |
| 4 | `04-c4.md` | C4 Architecture L1–L4 |
| 5 | `05-adrs.md` | Architecture Decision Records (20) |
| 6 | `06-microservices.md` | Microservices Architecture (10 services) |
| 7 | `07-database.md` | Database Architecture (PostgreSQL 18) |
| 8 | `08-security.md` | Security Architecture |
| 9 | `09-api-design.md` | API Design (+ `api/openapi.yaml`) |
| 10 | `10-workflows.md` | Workflow Architecture |
| 11 | `11-ux.md` | UX Architecture |
| 12 | `12-devops.md` | DevOps Architecture |
| 13 | `13-observability.md` | Observability |
| 14 | `14-scalability.md` | Scalability Architecture |
| 15 | `15-technology-adrs.md` | Technology ADRs (11) |
| 16 | `16-delivery-plan.md` | Delivery Plan |
| — | `appendix-acceptance-checklist.md` | Filled-in acceptance test harness |

Companion artefacts referenced by the sections:

- `api/openapi.yaml` — OpenAPI 3.1 specification (Section 9)
- `db/*.sql` — PostgreSQL 18 production DDL (Section 7)
- `src/` — .NET 10 reference implementation (Section 4 L4, Code Requirements)
- `infra/terraform/` — Terraform modules (Section 12)
- `deploy/helm/badge-service/` — Helm chart (Section 12)
- `.github/workflows/` (repo root) — CI/CD pipelines (Section 12)
- `observability/prometheus-alerts.yaml` — SLO burn-rate alert rules (Section 13)
