# ADR-0001 — Stack and project shape

- **Status:** Accepted (plan approved 2026-07-20)
- **Context:** Small team building the platform defined in `docs/02_PRD.md`; needs streaming
  LLM I/O, strong typing/validation, a compliance-friendly single data store, and a path from
  laptop → pilot without re-platforming.
- **Decision:**
  - Monorepo folder `ai_school_assistant/` with `backend/` (Python 3.12, FastAPI, Pydantic v2),
    `frontend/` (Next.js 15 + TypeScript), `infra/` (Docker Compose for dev, Terraform for cloud).
  - PostgreSQL 16 with **pgvector** as the only database (app data + embeddings + audit log);
    Redis for queues/cache (arq workers); S3-compatible object storage for uploads.
  - LLM access through a thin in-house `LLMGateway` over official provider SDKs — no
    LangChain-style framework (abstraction churn vs. ~300 lines we fully control).
  - Tailwind/shadcn deferred to Milestone 1 when real UI is built; M0 ships an unstyled shell.
  - CI on GitHub Actions: ruff + mypy(strict) + pytest for backend, `tsc --noEmit` for frontend;
    security scanning (pip-audit) added as dependencies grow.
- **Consequences:** One database to secure/back up (good for FERPA posture); pgvector must be
  re-evaluated if retrieval p95 exceeds 150 ms at scale (ADR to follow if we move to Qdrant).
  Runtime platform (Fly.io / Railway / ECS) is deliberately deferred to ADR-0002 at first
  cloud provisioning (Milestone 6).
