# Codex Master Instructions

> **Status: Constitution (binding).** Engineering charter for the AI School
> Assistant platform. Preserved as the source of truth; adoption decisions are
> in the [ADRs](../adr/). Where this charter and the
> [Master Implementation Specification](./MASTER_IMPLEMENTATION_SPECIFICATION.md)
> both apply, both must be satisfied.

## Mission
Build a production-ready Enterprise AI School Assistant platform. Never generate
demo-quality code. Everything must be production-ready.

## Engineering principles
Clean Architecture · Domain-Driven Design · SOLID · CQRS where appropriate ·
Event-Driven Architecture · API-First · Twelve-Factor · Secure by Design ·
Privacy by Design · Accessibility by Design · TDD where practical.

## Technology stack (authoritative)
- **Monorepo:** Turborepo + pnpm
- **Frontend:** Next.js + React + TypeScript + Tailwind CSS
- **Mobile:** Flutter + Dart
- **Backend:** NestJS + TypeScript
- **Data:** PostgreSQL · Redis (cache) · Qdrant (vectors) · OpenSearch (search)
- **Messaging:** NATS JetStream
- **AuthN/Z:** Keycloak · OAuth 2.1 · OIDC
- **Storage:** S3-compatible
- **Workflow:** Temporal
- **Infra:** Docker · Kubernetes · Helm · Terraform · ArgoCD
- **Observability:** OpenTelemetry · Prometheus · Grafana · Loki · Tempo
- **CI/CD:** GitHub Actions

Concrete pinned versions live in [`../STACK_VERSIONS.md`](../STACK_VERSIONS.md).

## Coding rules
Never: duplicate code · hardcode secrets/URLs · ignore architecture/tests/docs ·
mix layers · bypass dependency injection.
Always: reusable code · interfaces · DI · documented public APIs · input
validation · output sanitisation · structured logging.

## Security (every service)
AuthN · AuthZ · RBAC · ABAC when required · MFA support · rate limiting · audit
logging · encryption · secure config · secret management · input validation ·
output encoding. Never expose sensitive data.

## AI rules
AI providers must be abstracted. Support OpenAI, Anthropic, Google Gemini,
Mistral, Ollama, vLLM. Never couple business logic to one provider.
**(Reinforced by the Master Spec: never bypass the Capability Registry; always
use the AI SDK; every capability requires evaluation.)**

## API rules
Every service exposes REST · OpenAPI · health endpoint · metrics endpoint ·
versioning · pagination · filtering · sorting · a consistent error model.

## Database rules
Migrations · indexes · constraints · transactions · soft delete where
appropriate · audit fields · UUID identifiers. Never lose data.

## Testing rules
Unit · integration · contract · e2e · performance · security tests where
applicable. Coverage target **90%+**.

## Definition of Done
Code compiles · tests pass · lint passes · docs updated · security reviewed ·
performance acceptable · APIs documented · DB migrations included · CI passes.
See the consolidated, AI-aware DoD in [ADR-0003](../adr/0003-definition-of-done.md).

## Work-package workflow
Analyze → review architecture → review dependencies → implementation plan →
production code → tests → documentation → validate quality → implementation
summary → **wait for review**. Never continue to the next WP automatically.

## Absolute rules
Never skip tests · never skip documentation · never invent architecture · never
ignore security · never break previous modules · preserve backward compatibility
whenever possible.
