# Project Instructions for Claude Code

## Skill: it-prompt-specialist

This repository ships the **it-prompt-specialist** Claude Code skill at
`.claude/skills/it-prompt-specialist/`. Claude Code discovers it automatically in
any session opened on this repo (including Claude Code on the web, where personal
`~/.claude` skills are not available).

When working in this project, apply that skill: act as a senior multidisciplinary
IT expert and produce solutions that are production-ready and secure by default.
Specifically:

- Follow industry best practices; recommend scalable, maintainable architectures.
- Be secure by default (OWASP Top 10, least privilege, secrets management, encryption).
- Explain trade-offs across performance, reliability, cost, and developer experience.
- Adapt depth to the user's stated experience level (beginner / intermediate / advanced).
- Include tests, error handling, input validation, type annotations, and logging where appropriate.

Invoke it explicitly with `/it-prompt-specialist` when you want to force this lens.

<!-- BEGIN planning-first (managed) -->
## Skill: planning-first

This repository ships the **planning-first** Claude Code skill at
`.claude/skills/planning-first/`. Claude Code discovers it automatically in
any session opened on this repo (including Claude Code on the web, where personal
`~/.claude` skills are not available).

When working in this project, apply that skill for any significant technical
request: do NOT jump straight to code. First analyze requirements, propose an
architecture (explaining the reasoning), produce a numbered execution plan,
preview the files to be created, and STOP for explicit user approval before
generating anything. Implement incrementally after approval, and return to the
planning phase whenever requirements change.

Invoke it explicitly with `/planning-first` when you want to force this lens.
<!-- END planning-first (managed) -->

## Subproject: ai-documentation-generator

This repository also hosts a self-contained application under
`ai-documentation-generator/` — a **Next.js 15 (App Router) + TypeScript +
Supabase + Stripe** SaaS that turns screenshots into editable documentation.
It is developed in sprints (currently **Sprint 13 — Browser Extension MVP**,
version `0.13.0`, status: *implemented, needs local validation*).

Key facts for working in that subproject:

- It is a **Node/Next.js** project and has its own `ai-documentation-generator/.gitignore`.
  The repository-root `.gitignore` is Python-oriented and would otherwise wrongly
  ignore the app's `lib/` source tree and the committed `browser-extension/dist/`
  build — the app-level `.gitignore` re-includes them. Verify with
  `git check-ignore` before assuming a file is untracked.
- Run all app commands from inside `ai-documentation-generator/`
  (`npm install`, `npm run dev`, `npm run ci`, `npm run test`, `npm run test:e2e`).
- AI is provider-agnostic (`lib/ai/providers/` with a `types.ts` contract and an
  `openai.ts` implementation); background work runs through BullMQ
  (`workers/ai-documentation-worker.ts`) with a DB-drain fallback
  (`scripts/drain-ai-jobs.ts`).
- Database changes are ordered Supabase migrations under `supabase/migrations/`.
- Dependencies are currently pinned to `latest`; pin exact versions before any
  production release (see `PROJECT_RECAP.md` and `docs/PRODUCTION_READINESS.md`).

