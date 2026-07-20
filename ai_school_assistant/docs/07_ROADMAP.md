# 07 — Implementation Roadmap & Guide

Milestone-based plan (planning-first Phase 3–4). Estimates assume 1–2 developers.
**Every milestone ends with a demo + go/no-go checkpoint.**

## Phase overview

```
M0 Foundations → M1 Auth & Classes → M2 RAG Core → M3 Student Tutor
→ M4 Teacher Workbench → M5 Grading → M6 Insights & Safety Hardening
→ M7 Pilot → (approval) → v1.1 scale-out
```

---

## Milestone 0 — Foundations (Week 1)
**Objective:** repeatable, secure skeleton before any feature code.
**Deliverables:** monorepo scaffold (`backend/`, `frontend/`, `infra/`), Docker Compose dev
stack (Postgres+pgvector, Redis, MinIO), FastAPI healthcheck app, Next.js shell, CI (ruff,
mypy, pytest, pip-audit, secret scan), Terraform for the dev environment, `.env` handling via
secrets manager, ADR-0001 (stack) committed.
**Complexity:** Low · **Dependencies:** approved plan.

## Milestone 1 — Auth, Orgs & Classes (Weeks 2–3)
**Objective:** the security core.
**Deliverables:** email+Google SSO login, roles (teacher/student/admin), org/class/enrollment
models with **Postgres RLS policies + tests proving cross-class isolation**, invite codes,
class CRUD UI, audit-log table + middleware, rate limiting.
**Complexity:** Medium · **Depends on:** M0.
**Exit check:** a student in class A provably cannot read any class-B row (automated test).

## Milestone 2 — Content & RAG core (Weeks 3–4)
**Objective:** the grounding layer.
**Deliverables:** upload → parse (PDF/DOCX/MD) → chunk → embed → pgvector per-class index
(worker job with status UI); hybrid retrieval endpoint with citations; `LLMGateway`
(Anthropic SDK + Gemini fallback, router config, cost tracker, Langfuse tracing); prompt
registry; **grounding eval harness v1** with a 100-item seed set.
**Complexity:** Medium-High · **Depends on:** M1.
**Exit check:** grounding eval ≥ 85% (target 90% by M6); retrieval p95 < 150 ms.

## Milestone 3 — Student Tutor (Weeks 5–6)
**Objective:** the student hero feature, safely.
**Deliverables:** streaming chat UI with citations; Socratic system policy + hint-ladder
state; input/output moderation (Haiku); answer-leak guard v1; "I'm still stuck" escalation;
session summarizer/tagger; transcript viewer for teachers; **leak + jailbreak eval suites in CI**.
**Complexity:** High · **Depends on:** M2.
**Exit check:** leak eval ≤ 2% (target ≤1% by M6); first-token p95 < 2 s; red-team suite passes.

## Milestone 4 — Teacher Workbench: Lesson Planning (Week 7)
**Objective:** teacher hero feature.
**Deliverables:** lesson-plan generator (structured JSON output → section editor,
section-level regenerate), class library, export-to-clipboard/PDF.
**Complexity:** Medium · **Depends on:** M2.

## Milestone 5 — Draft Grading (Weeks 8–9)
**Objective:** the biggest time-savings claim.
**Deliverables:** assignment+rubric builder, submission intake (paste/CSV), batch grading
worker (Opus 4.8 Batch API), review UI (confidence sort, edit, approve), calibration store
(teacher deltas), rubric-agreement eval set.
**Complexity:** High · **Depends on:** M1, M2 (uses gateway/worker from M2).
**Exit check:** ≥ 80% within-1-point agreement on the 50-submission calibration set.

## Milestone 6 — Insight Loop & Hardening (Week 10)
**Objective:** close the loop; pass all quality gates.
**Deliverables:** weekly misconception digest (cluster + label + suggested re-teach →
one-click lesson generation), teacher dashboard, safety escalation SLA plumbing (alerts <5 min),
load test (200 concurrent chats), full eval-gate pass (03_MVP §4), security review
(OWASP ASVS L2 checklist), DPA/privacy-policy drafts, pilot onboarding docs.
**Complexity:** Medium-High · **Depends on:** M3, M5.

## Milestone 7 — Pilot (Weeks 11–14)
2–3 teachers, one subject, weekly feedback loop, feature kill-switches, cost dashboard watch.
**Exit:** journeys A–D exercised weekly; teachers would keep it; decision meeting → v1.1
backlog (quizzes, differentiation, multilingual, LMS export).

---

## Repository structure preview (Phase 4 — files to be created, on approval)

```
ai_school_assistant/
├── docs/                        # ← this planning package (done)
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, middleware, routers
│   │   ├── core/                # config, security (JWT/OIDC), rate limit, audit middleware
│   │   ├── models/              # SQLAlchemy models + Alembic migrations
│   │   ├── api/                 # routers: auth, classes, materials, tutor, grading, insights
│   │   ├── ai/
│   │   │   ├── gateway.py       # LLMGateway: routing, fallback, cost tracking
│   │   │   ├── prompts/         # versioned prompt templates (md + yaml)
│   │   │   ├── rag.py           # chunking, embedding, hybrid retrieval
│   │   │   ├── safety.py        # moderation, answer-leak guard, escalation
│   │   │   └── evals/           # golden sets + runners (CI-invoked)
│   │   └── workers/             # arq tasks: indexing, batch grading, digests
│   └── tests/                   # pytest: unit, RLS-isolation, API, eval smoke
├── frontend/
│   ├── package.json
│   └── src/app/                 # Next.js routes: (auth), teacher/, student/, admin/
├── infra/
│   ├── docker-compose.yml       # dev stack
│   └── terraform/               # cloud envs
└── .github/workflows/ci.yml     # lint, types, tests, security scans, eval gates
```

## Engineering ground rules (apply to every milestone)

1. **Tests with the feature, not after** — RLS-isolation and safety tests are release-blocking.
2. **Every AI behavior has an eval** before it ships; prompts change only via PR (versioned).
3. **Type annotations + Pydantic validation everywhere**; ruff/mypy clean is a merge gate.
4. **No secrets in code or compose files**; secrets manager from M0.
5. **Structured logging + trace on every LLM call** (model, prompt@ver, tokens, cost).
6. **ADRs** for every irreversible decision (stack, provider, data model changes).
7. **Incremental delivery** — each milestone is demoable and independently revertible.

## Risk register (roadmap-level)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Answer-leak guard hard to get <1% | Medium | High | Start eval set in M2; layered guard (policy+classifier+key-matching); cap = ship with stricter hint ceiling |
| PDF parsing quality on messy scans | High | Medium | MVP restricts to digital PDFs/DOCX; OCR deferred |
| Sonnet 5 intro pricing ends mid-build | Certain (2026-08-31) | Low | Cost model already uses full price |
| Teacher review fatigue → rubber-stamping | Medium | Medium | Confidence-sorted queue, edits tracked, pilot interviews |
| Scope creep toward LMS features | High | Medium | Non-goals list in PRD; checkpoint reviews per milestone |

---

## ✋ Phase 5 — Validation (STOP)

Per the planning-first workflow, implementation does **not** begin until explicit approval.

**Do you approve this architecture and implementation plan?**
- Approve as-is → build starts at Milestone 0.
- Request changes → plan is revised and re-submitted.
- Also welcome now: answers to the three open questions in 02_PRD §7 (target grade band,
  deployment preference, monetization) — none block M0–M2.
