# PROJECT_BLUEPRINT.md — Structure & Authoring Guide

Author `PROJECT_BLUEPRINT.md` following the 22 sections below, in order. Use hierarchical
Markdown headings. Every section must be present; write `N/A — not applicable to this project`
where a section genuinely does not apply, and `UNKNOWN — could not determine from repo` where
information exists but could not be recovered. Never invent facts to fill a section.

Describe **structure, contracts, algorithms, and decisions** — do not paste large code blocks.
Short illustrative snippets (a few lines) are allowed when a contract is clearer shown than told.

Start the document with a title, a one-paragraph abstract, and a metadata block
(generated date, generator = "Claude Code — Project Knowledge Exporter", commit/branch if known).

---

## 1. General Vision
Problem solved and business value · target users / personas · core features · secondary and
cross-cutting features · in-scope vs out-of-scope (functional and non-functional).

## 2. Global Architecture
Textual architecture overview (a C4-style Context → Container → Component walkthrough, ASCII
diagram encouraged). Cover, where present: frontend (framework, CSR/SSR/SSG, state management);
backend (monolith / modular / microservices, gateway/BFF); database (SQL/NoSQL, persistence
strategy); cache; message queue / broker; storage; authentication & authorization; notifications;
observability; infrastructure (Docker/K8s/serverless/VPS); and inter-service communication
(REST/gRPC/GraphQL/events). Omit layers that don't exist — say so.

## 3. Full Project Tree
The directory/file tree (significant files). For each folder: role, responsibility, typical
contents, naming convention, and the pattern it embodies (e.g. `domain/`, `application/`,
`infrastructure/` in DDD).

## 4. Modules / Services
For each module: name · single responsibility · interface contract (inputs/outputs, DTOs,
events) · inbound and outbound dependencies · stateful/stateless & lifecycle · required config.

## 5. Data Model
Entity–relationship description · tables/collections with columns, types, constraints, defaults ·
relations (1:1, 1:N, N:M) and foreign keys · indexes (primary, secondary, composite, full-text) ·
migration & versioning strategy · seeds/fixtures. `N/A` for projects with no persistence.

## 6. API Contract
For each endpoint (REST/GraphQL/gRPC/CLI command/public function): method & full path/signature ·
required headers (auth, content-type) · payload (body, query, path params) with types · responses
(success + error) with status codes and JSON shape · validation rules · rate limiting.

## 7. Business Workflows
Every critical workflow as an ordered sequence (auth/registration, main CRUD, complex business
processes, error handling & retries, long-running sagas). Name the actor for each step.

## 8. Business Rules
Every important rule in conditional form. Include invariants and cross-field validations:
```
IF   <condition>
THEN <expected behavior>
ELSE <alternative>
```

## 9. Patterns & Architectural Paradigms
Architectural style (Clean, Hexagonal, Layered, Modular Monolith, Microservices, MVC,
Event-Driven, …) and patterns in use (DDD building blocks, CQRS, Event Sourcing, Mediator,
Strategy, Factory, Repository, Dependency Injection, …). Tie each to where it appears in the code.

## 10. Architecture Decision Records (ADRs)
For each significant decision: title · status (proposed/accepted/deprecated) · context & problem ·
options considered (with pros/cons) · decision & rationale · consequences (positive and negative).

## 11. External Dependencies
Frameworks · key libraries (ORM, validation, HTTP client, …) · SDKs (AWS, Firebase, Stripe, …) ·
external APIs consumed · third-party services (Auth0, Clerk, Supabase, …). Pin versions where known.

## 12. Configuration & Environment
Environment variables (name, purpose, default, sensitivity — **names only, never values**) ·
secrets management approach · config files (`.env.example`, `config/*.yaml`) · multi-environment
strategy (dev/staging/prod) · Docker (Dockerfile, compose services/volumes/networks) · CI/CD
pipelines, stages, triggers · build & scripts.

## 13. Security
Authentication flow (JWT/OAuth2/sessions/MFA) · roles & permissions (RBAC/ABAC/ReBAC) · input
validation & sanitization · protections (CSRF, XSS, SQLi, rate limiting) · CORS/CSP/HSTS ·
audit & compliance (GDPR/HIPAA/SOC2) where relevant.

## 14. Performance & Scalability
Caching strategy (levels, TTL, keys, invalidation) · query optimization (indexes, eager/lazy
loading, pagination) · async processing (jobs, queues, workers) · scaling strategy (horizontal/
vertical/sharding).

## 15. Observability
Logging (levels, format, aggregation) · metrics (collection, dashboards, alerts) · distributed
tracing (OpenTelemetry/Jaeger/Datadog) · health/readiness probes.

## 16. Tests
Strategy (pyramid / testing trophy) · types present (unit, integration, E2E, snapshot,
performance) · coverage target vs actual (if known) · mocking strategy & fixtures · tooling.

## 17. Code Conventions
Naming (files, variables, functions, classes, components, constants) · import organization · lint/
format tooling · commit standard (e.g. Conventional Commits) · Git workflow (GitFlow/trunk-based).

## 18. Technical Debt & Known Limitations
Code to improve (and why) · fragile / tightly-coupled zones · under-tested areas · accepted
functional limitations · temporary workarounds. Be honest.

## 19. Roadmap & Planned Evolutions
Planned features (priority, status) · envisioned refactors · planned technical migrations ·
exploratory backlog ideas.

## 20. Reconstruction Guide
Step-by-step rebuild from scratch: (1) init repo & folder structure · (2) install dependencies ·
(3) configure environment · (4) set up database (migrations, seeds) · (5) run services
(backend, frontend, workers) · (6) verify (tests, health checks). Concrete and ordered.

## 21. LLM-Optimized Summary (Prompt Context)
A dense, compact block designed to be pasted into another LLM's context window: stack (one line),
architecture (2–3 sentences), main modules (list), critical conventions (short list), essential
business rules, and key design constraints. Optimize for minimal context loss.

## 22. Reconstruction Prompt
A ready-to-use, copy-paste prompt instructing a target LLM to rebuild the project. It must be
self-sufficient and include: clear instructions to the LLM · project context · imposed stack ·
architecture to respect · modules to implement (with specs) · data model · API contract ·
workflows to implement · conventions to follow · acceptance criteria.

---

### Quality bar for the blueprint
- Every section present; unknowns and N/A marked explicitly, never silently dropped.
- A reader with no repo access can understand and rebuild the project.
- Decisions are justified; business rules are exhaustive and unambiguous.
- Consistent with `PROJECT_CONTEXT.json` (same stack, modules, entities, rules).
- No secrets; only short illustrative code snippets.
