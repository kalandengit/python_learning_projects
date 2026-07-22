# Delivery Roadmap — Work Packages

Incremental, **bounded-context by bounded-context** (Master Spec). Each WP meets
the [Definition of Done](./adr/0003-definition-of-done.md) and stops for review
before the next (Codex §14). AI-native platform layers (AI SDK, Capability
Registry, Evaluation, Governance) are foundational and land early.

| WP | Title | Scope | Status |
|----|-------|-------|--------|
| **WP-0** | **Platform Foundation** | Turborepo + pnpm; shared packages (`@asa/config`, `@asa/logger`, `@asa/errors`, `@asa/contracts`); golden NestJS service template (health/live/ready, OpenAPI, `/metrics`, config, problem+json errors, pagination); local infra `docker-compose`; CI (lint/typecheck/test/build/scan); governance docs + ADRs | **in progress** |
| **WP-1** | Identity, Multi-tenancy & Access | Keycloak/OIDC gateway; RBAC/ABAC; tenant resolution + isolation; audit logging; MFA hooks | planned |
| **WP-2** | AI SDK + Capability Registry | Provider-agnostic AI SDK (OpenAI/Anthropic/Gemini/Mistral/Ollama/vLLM); Capability Registry (versioned capabilities, schemas); Evaluation + Governance + Observability hooks; MCP tool support | planned |
| **WP-3** | Agent Registry + Multi-Agent Runtime | Agent catalog, orchestration runtime, MCP-based tools | planned |
| **WP-4** | Eventing + Knowledge Platform | NATS JetStream + Event Catalog; Knowledge Platform (Qdrant/OpenSearch); Learner Digital Twin foundations | planned |
| **WP-5** | SIS (bounded context) | Students, enrollment — first domain on the template + platform | planned |
| **WP-6** | LMS (bounded context) | Courses, lessons, assignments, grading | planned |
| **WP-7+** | Portals & apps | Next.js web shell, Flutter shell; Teacher/Student/Parent portals; Finance; HR; AI Analytics | planned |
| **Cross-cutting** | Observability (OTel/Prom/Grafana/Loki/Tempo), IaC (Terraform/Helm/ArgoCD), security, AI Governance & Continuous Improvement Loop | threaded through every WP | ongoing |

## Gate policy
- No feature bounded context (WP-5+) ships AI before WP-2 exists — features
  consume **registered capabilities**, never raw model calls (ADR-0002).
- Each WP: plan → code → tests → docs → validate → summary → **review gate**.
