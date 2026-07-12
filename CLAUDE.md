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

<!-- BEGIN project-knowledge-exporter (managed) -->
## Skill: project-knowledge-exporter

This repository ships the **project-knowledge-exporter** Claude Code skill at
`.claude/skills/project-knowledge-exporter/`. Claude Code discovers it
automatically in any session opened on this repo (including Claude Code on the
web, where personal `~/.claude` skills are not available).

When asked to export project knowledge, document a codebase end-to-end, produce
a handoff/rebuild package, or preserve architecture and decisions, apply that
skill: first **investigate the repo** (tree, README/CLAUDE.md, manifests,
Docker/CI, source, models, APIs, tests, git history), then generate the five
knowledge files — `PROJECT_BLUEPRINT.md`, `PROJECT_CONTEXT.json`,
`PROJECT_REBUILD_PROMPT.md`, `DECISION_LOG.md`, and `DEVELOPMENT_STATE.md` —
grounded in what you found, labeling observed facts vs. inferences and avoiding
large source dumps.

Invoke it explicitly with `/project-knowledge-exporter` when you want to force
this lens.
<!-- END project-knowledge-exporter (managed) -->

<!-- BEGIN export_project (managed) -->
## Skill: export_project

This repository ships the **export_project** Claude Code skill at
`.claude/skills/export_project/` — the `/export_project` command, alias of
project-knowledge-exporter. Claude Code discovers it automatically in any
session opened on this repo (including Claude Code on the web, where personal
`~/.claude` skills are not available).

When the user runs `/export_project` or asks to export/snapshot/hand off the
project, apply that skill: first **investigate the repo** (tree,
README/CLAUDE.md, manifests, Docker/CI, source, models, APIs, tests, git
history), then generate the five knowledge files — `PROJECT_BLUEPRINT.md`,
`PROJECT_CONTEXT.json`, `PROJECT_REBUILD_PROMPT.md`, `DECISION_LOG.md`, and
`DEVELOPMENT_STATE.md` — grounded in what you found, labeling observed facts
vs. inferences and avoiding large source dumps.
<!-- END export_project (managed) -->

