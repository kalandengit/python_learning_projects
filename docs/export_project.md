# export_project — Claude Skill

A portable, self-contained copy of the **`export_project`** skill. It turns a
live software project into a durable, LLM-portable **Project Knowledge Package**
(five files) so the project can be understood, maintained, extended, and even
rebuilt if the original repo, git history, and conversations are lost.

## How to use this file

- **As a Claude Code skill (local sessions):** save the block below (from the
  opening `---` to the end) as `~/.claude/skills/export_project/SKILL.md`, then
  run `/export_project` in any project.
- **As a project skill:** save it as
  `.claude/skills/export_project/SKILL.md` in a repo; it auto-loads for anyone
  who opens that repo in Claude Code (including Claude Code on the web).
- **As a plain prompt (any chat — Claude.ai, ChatGPT, etc.):** ignore the
  `---` frontmatter and paste everything from `# Export Project` onward, then
  attach or connect the project's files so the model has something to analyze.

The deliverables it produces are: `PROJECT_BLUEPRINT.md`,
`PROJECT_CONTEXT.json`, `PROJECT_REBUILD_PROMPT.md`, `DECISION_LOG.md`, and
`DEVELOPMENT_STATE.md`.

---

<!-- ===== BEGIN SKILL.md (save this section as SKILL.md) ===== -->

---
name: export_project
description: Export a complete, durable, LLM-portable Project Knowledge Package for the current project — PROJECT_BLUEPRINT.md, PROJECT_CONTEXT.json, PROJECT_REBUILD_PROMPT.md, DECISION_LOG.md, and DEVELOPMENT_STATE.md — after actively investigating the repository. Use when the user runs /export_project or asks to export, snapshot, hand off, document, or preserve a project so another LLM or team can understand, maintain, extend, or rebuild it even if the original repo and history are lost.
when_to_use: The user runs /export_project, or asks to "export this project", "export project knowledge", "snapshot this codebase", "make a handoff/rebuild package", or "document this whole project so another LLM could rebuild it".
version: 1.0.0
author: kalandengit
---

# Export Project

## Purpose

Turn a live software project into a **durable engineering knowledge package** —
a small set of files that let another capable LLM (or engineering team)
understand, maintain, extend, and *reconstruct* the project with the highest
possible fidelity, **even if the original repository, git history, and
conversation history are gone.**

The goal is **knowledge preservation and project reconstruction**, not a
summary. Reconstruct the project's *engineering knowledge*: intent,
architecture, responsibilities, interfaces, data flow, and rationale — while
avoiding large dumps of source code.

Assume that after this export the repo may vanish, chats may be lost, and future
development may be done by a different LLM or team. Preserve everything they
would need to continue.

---

## How this skill runs in Claude Code (important)

Unlike a chat-only assistant that can only see whatever was pasted, **Claude Code
can read the real project.** Do not rely on memory or on the user pasting code.
**Investigate first, write second.** Ground every claim in files you actually
opened.

### Phase 0 — Discovery (always do this before generating anything)

Explore the repository with your tools before drafting any deliverable:

1. **Map the tree** — list directories; identify entry points, config, and where
   code vs. docs vs. infra live. Respect `.gitignore`; skip `node_modules`,
   build output, and vendored code.
2. **Read the signals** — `README*`, `CLAUDE.md`, `package.json` /
   `pyproject.toml` / `go.mod` / `Cargo.toml` / `pom.xml`, lockfiles,
   `Dockerfile`, `docker-compose*`, `.github/workflows`, `Makefile`, `.env.example`,
   migrations, and any `docs/` or ADRs.
3. **Trace the code** — open the main modules, routers/controllers, models/schemas,
   services, and tests. Follow imports to build a real dependency picture. Use
   search to find endpoints, entities, env-var reads, and background jobs.
4. **Read git context if present** — recent commit messages, branches, and tags
   often reveal intent, roadmap, and in-flight work. If git history is absent,
   note that and rely on code + config.
5. **Detect the domain and conventions** — naming, folder layout, error-handling
   style, logging, test patterns. Capture the *implicit* conventions, not just
   the explicit ones.

Adapt scope to the project's size and stack. A CLI tool, a library, a web app,
and a monorepo each deserve emphasis on different sections below — include what
applies, and say when a standard section is **N/A** rather than inventing content.

### Phase 1 — Generate the deliverables

Only after discovery, write the five files below into the project (default
location: repo root, or a `knowledge-export/` folder if the user prefers).
Confirm the target location if it's ambiguous.

---

## Deliverables

Generate these five files.

### 1. `PROJECT_BLUEPRINT.md`
The complete functional + technical blueprint. Include, where applicable:
executive summary, product vision, functional overview, architecture,
components, domain model, APIs, infrastructure, business rules, design
decisions, deployment, security, and scalability. Use Mermaid diagrams for
architecture, sequence flows, ER diagrams, and component interactions.

### 2. `PROJECT_CONTEXT.json`
A structured, LLM-ingestible representation of the project. Must be **valid
JSON** and include at least these top-level keys:

```json
{
  "metadata": {},
  "architecture": {},
  "technologies": {},
  "modules": [],
  "entities": [],
  "apis": [],
  "workflows": [],
  "business_rules": [],
  "dependencies": [],
  "coding_conventions": [],
  "deployment": {},
  "roadmap": {},
  "known_limitations": [],
  "technical_debt": [],
  "engineering_decisions": []
}
```

Keep values concise and machine-friendly (short strings, arrays, nested
objects). This file is optimized for another LLM to ingest — it is the
structured twin of the blueprint.

### 3. `PROJECT_REBUILD_PROMPT.md`
A complete **Master Prompt** another LLM session can use to rebuild the entire
project from scratch. Include: context, goals, product vision, functional
requirements, architecture, stack, database, APIs, modules, workflows, coding
conventions, constraints, security, performance expectations, deployment, and
roadmap. Write it as a directly reusable prompt, not as a description of one.

### 4. `DECISION_LOG.md`
Every major engineering decision, in ADR style. For each: **Decision,
Motivation, Alternatives considered, Trade-offs, Consequences.** Prefer
decisions you can evidence from the code/config; clearly mark reasonable
inferences as inferred.

### 5. `DEVELOPMENT_STATE.md`
The current state of development: completed work, remaining work, known bugs,
technical debt, missing features, planned improvements, and risks. This is the
"where we are and what's next" handoff.

---

## What to capture (analysis checklist)

Cover the following as they apply to the project. Omit or mark **N/A** what
genuinely doesn't apply — do not pad.

1. **Product** — purpose, business objectives, target users, core problem, main
   and secondary functionality.
2. **Architecture** — frontend, backend, services, databases, auth/authz,
   queues, caching, AI modules, notifications, monitoring, logging,
   infrastructure, and how components interact.
3. **Repository organization** — for each major directory: purpose,
   responsibility, important files, relationships.
4. **Modules** — for each: purpose, responsibilities, inputs, outputs,
   interfaces, dependencies, internal workflow, error handling.
5. **Data model** — entities, tables, relationships, constraints, indexes,
   migrations, data ownership, and lifecycle.
6. **APIs** — for each endpoint: route, method, auth, request body, response
   body, validation, and errors.
7. **Workflows** — describe end-to-end flows (auth, registration, CRUD,
   notifications, AI processing, alerts, background/scheduled jobs) as ordered
   steps; use Mermaid sequence diagrams where it clarifies.
8. **Business rules** — express important rules as `IF … THEN … ELSE` where
   possible.
9. **Engineering patterns** — identify patterns actually present (Clean
   Architecture, DDD, CQRS, MVC/MVVM, Hexagonal/Onion, Repository, Strategy,
   Factory, DI, event-driven, …) and where each is used.
10. **Engineering decisions** — why this architecture, framework, database, and
    key libraries; which alternatives were plausible.
11. **Dependencies** — frameworks, libraries, SDKs, external APIs, cloud
    services, and why each exists.
12. **Configuration** — environment variables, build config, Docker/Compose/K8s,
    CI/CD, and deployment scripts.
13. **Security** — authentication, authorization/RBAC, JWT/OAuth, secrets
    management, validation, encryption, and best practices in use (or missing).
14. **Performance** — caching, DB optimization, async processing, queues,
    scaling strategy, and bottlenecks.
15. **Observability** — logging, metrics, monitoring, tracing, alerting.
16. **Testing** — unit/integration/e2e, coverage, and overall strategy.
17. **Coding standards** — naming, folder organization, style, error handling,
    formatting, linting, documentation standards.
18. **Technical debt** — weak areas, risks, refactoring opportunities, missing
    docs, performance concerns.
19. **Roadmap** — short / mid / long-term and scaling strategy.
20. **Reconstruction guide** — ordered steps: infrastructure → environment →
    database → backend → frontend → auth → APIs → business logic → testing →
    deployment.
21. **LLM knowledge summary** — a dense but readable summary (architecture,
    components, business logic, data model, APIs, workflows, decisions,
    constraints) that fits a reasonable context window with maximum information
    density. Include this inside `PROJECT_BLUEPRINT.md` (or as a top section of
    `PROJECT_CONTEXT.json` metadata).

---

## Rigor and honesty rules

1. **Facts vs. inferences** — clearly label what you observed in the code versus
   what you reasonably inferred. Never present a guess as a verified fact.
2. **Preserve intent**, not just implementation details.
3. **Explain the reasoning** behind architectural and design choices.
4. **Connect modules into coherent end-to-end workflows** — don't leave a bag of
   disconnected parts.
5. **Surface inconsistencies, risks, and improvement opportunities** rather than
   glossing over them.
6. **Compress without losing essential technical context.** Avoid reproducing
   large blocks of source; capture intent, interfaces, algorithms, and data
   flow instead.
7. **Do not invent** features, endpoints, or infrastructure that aren't in the
   project. If something important is unknowable from the repo, say so
   explicitly in `DEVELOPMENT_STATE.md` under risks/unknowns.
8. **Keep `PROJECT_CONTEXT.json` valid** — validate the JSON before finishing.

---

## Output standards

The package must be self-contained, complete, technically accurate, well
structured, and easy to maintain, extend, and reuse — optimized for both humans
and LLMs. Favor structured Markdown (clear headings, tables) and Mermaid
diagrams. After writing, do a quick consistency pass: the blueprint, the JSON,
and the rebuild prompt should agree with each other.

## Final objective

A durable engineering knowledge package that lets Claude — or another capable
LLM — understand, maintain, extend, and reconstruct the project with the highest
possible fidelity, even when the original repository and conversation history
are unavailable.

<!-- ===== END SKILL.md ===== -->
