# AI School Assistant

An integrated AI teacher & student assistant: teacher workbench (lesson planning, draft
grading, differentiation) + a Socratic student tutor grounded in the teacher's own
curriculum + a misconception-insight loop back to the teacher.

📋 **Planning package:** [`docs/`](docs/README.md) — PRD, MVP, architecture, workflows,
LLM selection, roadmap. **Current status: Milestone 0 (foundations) implemented.**

## Layout

```
backend/    FastAPI API (Python 3.12) — app factory, config, health endpoints, tests
frontend/   Next.js 15 shell (TypeScript)
infra/      docker-compose dev stack (Postgres+pgvector, Redis, MinIO) + Terraform skeleton
docs/       planning package + ADRs
```

## Local development

Backend (no infra needed for M0):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # smoke tests
uvicorn app.main:app --reload   # http://localhost:8000/healthz, /docs
```

Full dev stack (DB, Redis, object store, API container):

```bash
docker compose -f infra/docker-compose.yml up -d
```

Frontend:

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

Configuration: copy `.env.example` → `backend/.env`. Never commit real secrets.

## Quality gates

CI runs ruff, mypy (strict), pytest, and frontend typecheck on every PR touching
`ai_school_assistant/`. AI-behavior changes additionally run the eval suites
(from Milestone 2 — see `docs/03_MVP.md` §4).
