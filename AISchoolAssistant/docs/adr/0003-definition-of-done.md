# ADR-0003: Consolidated Definition of Done + evaluation/governance gates

- **Status:** Accepted
- **Date:** 2026-07-22
- **Context:** Codex §12 Definition of Done + Master Spec #9–#13

## Decision
A change is **Done** only when all gates pass. CI enforces the automatable ones;
reviewers enforce the rest.

### Universal gates (every change)
- [ ] Code compiles (`turbo build`) and typechecks (`turbo typecheck`).
- [ ] Lint passes with **zero warnings** (`turbo lint`).
- [ ] Formatting clean (`prettier --check`).
- [ ] Tests pass; **coverage ≥ 90%** on changed packages (unit + integration; e2e where applicable).
- [ ] Public APIs documented (OpenAPI) + README/docs updated + CHANGELOG entry.
- [ ] Security reviewed (authz, input validation, secrets, output encoding); dependency + secret scan clean.
- [ ] DB changes ship with **migrations** (no `synchronize` in prod), audit fields, UUID keys.
- [ ] Observability present: structured logs, metrics, health/live/ready, traces.
- [ ] Backward compatibility preserved (or a documented, versioned migration path).

### AI capability gates (any change touching AI)
- [ ] AI accessed **only** through the AI SDK via a **registered capability** (no direct provider calls).
- [ ] The capability has an **evaluation suite** (accuracy + safety + regression) that passes threshold.
- [ ] Governance metadata complete (owner, data classification, PII policy, model allow-list).
- [ ] Capability invocations are traced and emit Event-Catalog events (AI Observability).

## Motivation
Encodes the constitution's hard rules ("every feature requires tests/docs",
"every capability requires evaluation") into a single checklist the PR template
and CI reference, so nothing is skipped.

## Consequences
- The PR template mirrors this checklist (§13).
- CI blocks merges failing any automatable gate.
- "Evaluation-less" capabilities cannot be promoted past `draft`.
