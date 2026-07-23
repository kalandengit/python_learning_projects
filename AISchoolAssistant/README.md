# AI School Assistant Platform

Enterprise, AI-native education platform (SIS, LMS, teacher/student/parent
portals, AI tutors & assistants, analytics) built as a Turborepo monorepo.

> **Constitution:** [`docs/governance/MASTER_IMPLEMENTATION_SPECIFICATION.md`](docs/governance/MASTER_IMPLEMENTATION_SPECIFICATION.md)
> and [`docs/governance/CODEX_MASTER_INSTRUCTIONS.md`](docs/governance/CODEX_MASTER_INSTRUCTIONS.md).
> Adoption decisions: [`docs/adr/`](docs/adr/). Delivery plan: [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Principles

Clean Architecture · DDD · SOLID · CQRS where apt · Event-Driven · API-First ·
Twelve-Factor · Secure/Privacy/Accessibility by Design. **AI-native:** all AI
flows through the AI SDK and a registered **Capability** — never a raw provider
call (ADR-0002).

## Repository layout

```
AISchoolAssistant/
├── apps/                # Next.js web, Flutter mobile (later WPs)
├── services/            # NestJS services (from the golden template)
│   └── service-template/
├── packages/            # shared libs: @asa/config, @asa/logger, @asa/errors, @asa/contracts, @asa/auth, @asa/ai-sdk, @asa/capability-registry
├── infrastructure/      # docker-compose (dev), Helm/Terraform (later)
├── docs/                # governance, ADRs, roadmap, stack versions
├── scripts/
└── .github/workflows/
```

## Getting started (WP-0)

```bash
corepack enable
pnpm install
pnpm build && pnpm lint && pnpm typecheck && pnpm test
# Local infrastructure (Postgres, Redis, NATS, Keycloak, Qdrant, OpenSearch, Temporal, MinIO):
docker compose -f infrastructure/docker-compose.dev.yml up -d
# Run the golden service:
pnpm --filter @asa/service-template start:dev   # http://localhost:3000/api/v1/health/live
```

## Toolchain

Node 22+/24 LTS · pnpm 11 · Turborepo 2 · TypeScript 5.9 · NestJS 11.
Pinned versions & upgrade policy: [`docs/STACK_VERSIONS.md`](docs/STACK_VERSIONS.md).

## Status

**WP-0 (Platform Foundation)** — see [`docs/ROADMAP.md`](docs/ROADMAP.md).
