# Delivery Roadmap — Work Packages

Incremental, **bounded-context by bounded-context** (Master Spec). Each WP meets
the [Definition of Done](./adr/0003-definition-of-done.md) and stops for review
before the next (Codex §14). AI-native platform layers (AI SDK, Capability
Registry, Evaluation, Governance) are foundational and land early.

| WP | Title | Scope | Status |
|----|-------|-------|--------|
| **WP-0** | **Platform Foundation** | Turborepo + pnpm; shared packages (`@asa/config`, `@asa/logger`, `@asa/errors`, `@asa/contracts`); golden NestJS service template (health/live/ready, OpenAPI, `/metrics`, config, problem+json errors, pagination); local infra `docker-compose`; CI (lint/typecheck/test/build/scan); governance docs + ADRs | **done** |
| **WP-1** | **Identity, Multi-tenancy & Access** | `@asa/auth`: OIDC/OAuth 2.1 JWT verification (Keycloak JWKS, RS256); RBAC guards + `@Roles`/`@Public`; `@CurrentUser`/`@CurrentTenant`; `AsyncLocalStorage` request context (tenant + correlation id); wired into the service template with e2e coverage (ADR-0004) | **done** |
| **WP-2** | **AI SDK + Capability Registry** | `@asa/ai-sdk` (provider port, provider registry, model router, deterministic EchoProvider); `@asa/capability-registry` (versioned capabilities w/ zod I/O schemas, governance + model allow-list, evaluation-gated publish, governed executor, observability sink, NestJS `AiModule` w/ boot-time publish); reference `faq-answer` capability wired into the service template with e2e (ADR-0002). Vendor adapters + MCP tools follow. | **done** |
| **WP-3** | **Agent Registry + Multi-Agent Runtime** | `@asa/agent-runtime`: Tool Registry (JSON-Schema + zod-validated args) + Agent Registry (versioned agents, tool allow-list, maxSteps, governance) + `AgentExecutor` bounded tool-calling loop + observability; `ScriptedProvider` for deterministic tests; reference `assistant` agent + `add` tool + `POST /api/v1/agents/:id/invoke` wired into the service template with e2e (ADR-0005). MCP + capability-backed tools follow. | **done** |
| **WP-4** | Eventing + Knowledge Platform | NATS JetStream + Event Catalog; Knowledge Platform (Qdrant/OpenSearch); Learner Digital Twin foundations | planned |
| **WP-5** | SIS (bounded context) | Students, enrollment — first domain on the template + platform | planned |
| **WP-6** | LMS (bounded context) | Courses, lessons, assignments, grading | planned |
| **WP-7+** | Portals & apps | Next.js web shell, Flutter shell; Teacher/Student/Parent portals; Finance; HR; AI Analytics | planned |
| **Cross-cutting** | Observability (OTel/Prom/Grafana/Loki/Tempo), IaC (Terraform/Helm/ArgoCD), security, AI Governance & Continuous Improvement Loop | threaded through every WP | ongoing |

## Gate policy
- No feature bounded context (WP-5+) ships AI before WP-2 exists — features
  consume **registered capabilities**, never raw model calls (ADR-0002).
- Each WP: plan → code → tests → docs → validate → summary → **review gate**.
