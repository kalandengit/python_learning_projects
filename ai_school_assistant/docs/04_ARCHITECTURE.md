# 04 — Architecture Design

**Principles:** boring-first (managed services, monolith-until-it-hurts), secure by default,
LLM-provider-agnostic core, everything auditable, graceful AI degradation.

## 1. System overview

```
                          ┌────────────────────────────────────────────┐
                          │                Next.js Web App             │
                          │  Teacher Workbench │ Student Tutor │ Admin │
                          └───────────────┬────────────────────────────┘
                                          │ HTTPS (REST + SSE streaming)
                          ┌───────────────▼────────────────────────────┐
                          │            FastAPI Backend (Python)        │
                          │ ┌───────────┐ ┌──────────┐ ┌────────────┐  │
                          │ │ Auth/RBAC │ │ Classes/ │ │  Audit &   │  │
                          │ │ (JWT+SSO) │ │ Content  │ │  Metrics   │  │
                          │ └───────────┘ └──────────┘ └────────────┘  │
                          │ ┌────────────────────────────────────────┐ │
                          │ │            AI Orchestration Layer      │ │
                          │ │  Prompt registry · Model router ·      │ │
                          │ │  RAG pipeline · Safety pipeline ·      │ │
                          │ │  Eval hooks · Cost tracker             │ │
                          │ └───────┬───────────────┬────────────────┘ │
                          └─────────┼───────────────┼──────────────────┘
                 ┌────────────────┐ │               │ ┌───────────────────────┐
                 │ Worker (arq/   │◄┘               └►│  LLM Providers        │
                 │ Celery + Redis)│  batch grading,    │  Anthropic (primary)  │
                 │                │  indexing, digests │  fallback: Gemini/GPT │
                 └───────┬────────┘                    └───────────────────────┘
                         │
        ┌────────────────▼───────────────────────────────┐
        │ PostgreSQL (+ pgvector)  │  Redis  │ S3-compat │
        │ app data · embeddings ·  │ cache/  │ file blobs│
        │ transcripts · audit log  │ queues  │ uploads   │
        └────────────────────────────────────────────────┘
```

## 2. Component decisions & trade-offs

| Component | Choice | Why (trade-offs considered) |
|-----------|--------|------------------------------|
| Backend | **Python 3.12 + FastAPI** | Async-native (LLM streaming), Pydantic validation everywhere, best AI-ecosystem fit; repo is a Python project. Considered Node/Nest (fine, weaker AI tooling) and Django (batteries, but sync-first). |
| Frontend | **Next.js 15 + TypeScript + Tailwind + shadcn/ui** | SSR for fast loads on school hardware, streaming UI support, huge component ecosystem. Considered SvelteKit (leaner, smaller hiring pool). |
| Primary DB | **PostgreSQL 16** | Relational fits classes/assignments/rubrics; RLS available for tenant isolation. |
| Vector store | **pgvector** (in Postgres) | One database to secure/back up/comply; at MVP scale (<10M chunks) performance is fine with HNSW. Considered Qdrant/Pinecone — revisit only if retrieval p95 > 150 ms at scale. |
| Queue/cache | **Redis + arq** | Batch grading, indexing, digests; simplest Python-async worker. Celery if we outgrow it. |
| File storage | **S3-compatible object storage** | Uploads, exports; presigned URLs, server-side encryption. |
| Doc parsing | **unstructured / pymupdf + python-docx/pptx** | Robust PDF/Office extraction; OCR (later) via managed API. |
| LLM access | **Official provider SDKs behind our own thin `LLMGateway` interface** | Provider-agnostic routing/fallback without a heavyweight framework. Considered LangChain (abstraction tax, churn) — we use plain SDKs + our registry. |
| Observability | **OpenTelemetry + Langfuse (self-host) + Sentry** | Per-call traces with prompt/model/tokens/cost; error tracking. |
| Deployment | **Docker → single cloud region: managed Postgres + Redis, app on Fly.io/Railway/ECS** | No Kubernetes at MVP. Terraform IaC from day one for reproducibility. |
| CI/CD | **GitHub Actions**: lint (ruff), types (mypy/pyright), tests (pytest), deps audit (pip-audit), secret scan, eval suite on AI-touching PRs | Quality + security gates automated. |

## 3. AI Orchestration Layer (the core IP)

### 3.1 Prompt registry
- Versioned prompt templates in-repo (`prompts/*.md` + YAML metadata), loaded at startup.
- Every LLM call logs `prompt_id@version + model + params` to the audit log → reproducibility.

### 3.2 Model router
- Task-class → model mapping in config (see 06_LLM_SELECTION): tutor turns → Sonnet 5;
  lesson/grading generation → Opus 4.8; moderation/classification/routing → Haiku 4.5.
- Per-provider circuit breaker + fallback chain (Anthropic → Gemini) with health checks.
- Cost tracker: per-org, per-feature token accounting; soft budget alerts, hard caps per org.

### 3.3 RAG pipeline
```
upload → parse → clean → chunk (heading-aware, ~500 tok, 15% overlap)
       → embed (provider embedding API) → pgvector (per-class namespace)

query → class-scoped hybrid retrieval (vector + BM25/tsvector) → rerank (LLM-lite)
      → top-k (6) with source spans → prompt assembly with citation markers
```
- **Isolation rule:** retrieval is always filtered by `class_id` the requester is enrolled
  in — enforced in SQL (RLS), not just app code.
- Citations returned as `[source: unit3.pdf §2.1]` and rendered as links.
- Prompt caching: the per-class stable context (persona + class profile + policy) is placed
  as a cached prefix — large cost/latency win on chatty tutor sessions.

### 3.4 Safety pipeline (every student-facing call)
```
user msg → input moderation (Haiku classifier + rules)        [block/flag/pass]
         → tutor generation (Socratic system policy, RAG)
         → output guards: moderation + answer-leak check       [rewrite/block/pass]
         → log + (if flagged) escalation event → teacher alert
```
- Answer-leak check: compare candidate output against active assignment answer keys /
  solution patterns (embedding similarity + rules); on hit, regenerate with stricter hint level.
- Jailbreak resistance: system prompt hardening + input classifier + output classifier;
  red-team suite in CI.

### 3.5 Eval harness
- Golden datasets per feature (grounding, leak, rubric agreement, moderation).
- Runs in CI on prompt/model/router changes; results gate merge (thresholds from 03_MVP §4).

## 4. Data model (core entities)

```
Org ─┬─ User (role: teacher|student|admin)
     └─ Class ─┬─ Enrollment(user, class, role)
               ├─ Material ── Chunk(embedding, span)          [pgvector]
               ├─ Assignment ── Rubric ── Criterion
               │      └─ Submission ── DraftGrade ── ApprovedGrade
               ├─ TutorSession ── TutorMessage(citations, flags, mastery_signal)
               ├─ Escalation(status, resolved_by)
               └─ InsightDigest(week, clusters)
AuditEvent(actor, action, entity, model, prompt_ver, tokens, cost, ts)   [append-only]
```

## 5. Security architecture

- **AuthN:** OIDC (Google Workspace for Education) + email/password (argon2); short-lived JWT
  access + rotating refresh tokens; session revocation.
- **AuthZ:** role- and class-scoped; Postgres **Row-Level Security** as a second enforcement
  layer for all class-partitioned tables.
- **Tenant isolation:** single DB, org_id/class_id RLS policies; option to shard per district later.
- **Secrets:** cloud secrets manager; no secrets in env files in repo; key rotation runbook.
- **Encryption:** TLS 1.3; AES-256 at rest (DB, object storage); field-level encryption for
  the few direct identifiers (student name/email).
- **PII minimization:** analytics and eval datasets use pseudonymous IDs; transcripts
  purgeable per retention policy (default 12 months) and on request.
- **LLM data posture:** provider agreements with no-training-on-inputs; no student PII in
  prompts beyond first name; provider data-retention settings documented in the DPA.
- **OWASP:** ASVS L2 checklist tracked in repo; input validation via Pydantic; rate limiting
  (per-user, per-org) at the gateway; CSP + CSRF protections on the web app; dependency and
  container scanning in CI.
- **Audit:** append-only `AuditEvent` for every AI generation, approval, deletion, and admin
  action — exportable for district review.

## 6. Scalability path

| Stage | Trigger | Change |
|-------|---------|--------|
| MVP | — | Single region, 2 app instances, managed PG + Redis |
| Growth | >5k DAU or retrieval p95 >150 ms | Read replicas; dedicated vector DB (Qdrant); CDN for assets |
| Scale | >50k DAU / multi-district SLAs | ECS/K8s, multi-AZ, per-district data residency options, provider-level rate-limit tiering |

## 7. Failure modes & degradation

| Failure | Behavior |
|---------|----------|
| LLM provider outage | Router falls back to secondary provider; if all down: tutor shows "assistant unavailable", teacher tools queue jobs |
| Moderation service degraded | Fail **closed** for students (block + notify), fail open for teacher-only drafting with banner |
| Vector index stale/corrupt | Tutor answers with "materials unavailable" honesty mode (no ungrounded answering); reindex job |
| Cost cap hit (org) | Tutor rate-limited with friendly message; teacher tools switch to batch-only |
