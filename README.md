# python_learning_projects

A monorepo hosting two independent things by [@kalandengit](https://github.com/kalandengit):

1. A **Claude Code skills marketplace** (`planning-first`, `it-prompt-specialist`).
2. The **AI Documentation Generator** application (`ai-documentation-generator/`).

## Contents

| Path | What it is |
| ---- | ---------- |
| `.claude/skills/` | Skills auto-discovered in Claude Code sessions opened on this repo. |
| `claude-skills/` | The same skills packaged as a publishable Claude Code **plugin marketplace** bundle. |
| `.claude-plugin/marketplace.json` | Marketplace catalog. Add with `/plugin marketplace add kalandengit/python_learning_projects`. |
| `scripts/` | Install/publish helpers for the skills. |
| `ai-documentation-generator/` | Next.js 15 + Supabase + Stripe SaaS that turns screenshots into editable documentation. |

## Claude Code skills

| Skill | What it does |
| ----- | ------------ |
| **planning-first** | Forces a plan-first workflow — analyze requirements, propose an architecture, present an execution plan + files preview, and get explicit approval **before** writing any code or files. |
| **it-prompt-specialist** | A senior multidisciplinary IT expert lens across software, cloud, security, AI/ML, networking, embedded, game dev, and project management. |

Invoke a skill with `/planning-first` or `/it-prompt-specialist`, or just describe
a task and Claude activates the relevant skill automatically. See
`claude-skills/README.md` for marketplace install instructions.

## AI Documentation Generator

A production-oriented AI SaaS (Next.js App Router, TypeScript, Tailwind, Supabase
Auth/Postgres/Storage/RLS, Stripe billing, OpenAI vision, BullMQ background jobs,
and a Manifest V3 browser extension). Currently at **Sprint 13 — Browser Extension
MVP** (`v0.13.0`), *implemented and pending local validation*.

```bash
cd ai-documentation-generator
npm install
cp .env.example .env.local   # fill in Supabase / Stripe / OpenAI keys
npm run dev
```

Full details, environment variables, and per-sprint history live in
`ai-documentation-generator/README.md`, `PROJECT_RECAP.md`, and `docs/`.

> **Note on `.gitignore`:** the repository root `.gitignore` is Python-oriented.
> The app therefore carries its own `ai-documentation-generator/.gitignore` that
> re-includes the app's `lib/` source and committed `browser-extension/dist/`
> build (which the root file would otherwise ignore) and applies proper Node/Next
> ignore rules.

## License

MIT (see `LICENSE`).
