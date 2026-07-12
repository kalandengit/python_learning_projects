# PROJECT_REBUILD_PROMPT

> Paste everything below this line into a fresh LLM session (Claude Code
> recommended) to rebuild this repository from scratch with high fidelity.

---

You are rebuilding a **Claude Code skills distribution repository** named
`python_learning_projects` (owner: `kalandengit`; the name is historical — the
repo contains no Python, only skill Markdown, JSON manifests, and bash
installers). Recreate the structure, conventions, and content described below
exactly.

## Goal

Author reusable Claude Code *skills* and distribute each one through three
parallel channels so it works in every Claude surface:

1. **In-repo auto-discovery** — `.claude/skills/<skill>/SKILL.md` (canonical
   copy; works in local sessions and Claude Code on the web).
2. **Plugin marketplace** — the repo itself is a marketplace (name
   `kalandengit-skills`) via root `.claude-plugin/marketplace.json` whose
   plugin `source` paths point into `./claude-skills/plugins/...`; additionally
   `claude-skills/` is a self-contained publishable bundle with its own
   `marketplace.json` (sources `./plugins/...`), README, and MIT LICENSE.
3. **Standalone copies + installers** — `skills/<skill>/{SKILL.md, README.md}`
   for curl installs into `~/.claude/skills/` or claude.ai zip upload, plus
   `scripts/install-<plugin>.sh` per skill.

## Repository layout to create

```
.claude/skills/{it-prompt-specialist,planning-first,project-knowledge-exporter,export_project}/SKILL.md
.claude-plugin/marketplace.json
claude-skills/
    .claude-plugin/marketplace.json
    README.md            # marketplace docs: skills table, install commands, layout
    LICENSE              # MIT
    plugins/<plugin>/
        .claude-plugin/plugin.json
        skills/<skill>/SKILL.md
skills/<skill>/{SKILL.md, README.md}
scripts/install-{it-prompt-specialist,planning-first,project-knowledge-exporter,export-project}.sh
scripts/publish-claude-skills.sh
CLAUDE.md                # one section per skill; some in managed BEGIN/END blocks
README.md                # (currently a placeholder: "# python_learning_projects")
LICENSE                  # currently GPLv3 at root — known inconsistency vs MIT elsewhere
.gitignore               # standard Python gitignore (legacy)
```

## The four skills (recreate each SKILL.md)

Frontmatter schema for every skill: `name`, `description` (rich, includes
"Use when..." triggers), optional `when_to_use` (trigger phrases), `version:
1.0.0`, `author`.

1. **`it-prompt-specialist`** (author: OpenAI) — makes Claude act as a senior
   multidisciplinary IT expert (long role list from software dev through
   cybersecurity, cloud, data, UX, embedded, game dev). Sections: primary
   objectives (accuracy, best practices, scalability, trade-offs, security,
   cost, DX); response style adapted to beginner/intermediate/advanced; coding
   standards (production-ready, typed, validated, logged, error-handled);
   supported languages/frameworks lists; cybersecurity (OWASP Top 10, Zero
   Trust, least privilege, secrets, encryption; never recommend insecure
   practices); architecture guidance; troubleshooting mode (6 numbered steps);
   code-review mode; documentation mode; project management; AI/ML (RAG,
   agents, MCP, MLOps); UX/UI (WCAG); networking; embedded; game dev; best
   practices; and a closing French-language context section explaining the
   prompt's intent.

2. **`planning-first`** (author: OpenAI; French description in frontmatter) —
   forbids jumping straight to code for any significant build request.
   Mandatory phases: (1) requirement analysis (objective, functional/
   non-functional, assumptions, missing info, risks, constraints — ask
   questions if info missing); (2) architecture proposal with reasoning;
   (3) numbered execution plan (objectives, deliverables, dependencies,
   complexity per step); (4) files preview (full tree + purpose of every file,
   generate nothing yet); (5) validation — STOP and ask "Do you approve this
   architecture and implementation plan?", proceed only on explicit yes;
   (6) incremental implementation in stages, milestones for >10-file projects,
   re-plan + re-approve on requirement changes. Forbidden: generating whole
   projects at once, inventing requirements, skipping validation.

3. **`project-knowledge-exporter`** (author: kalandengit) — two-phase workflow.
   Phase 0 Discovery: map the tree; read README/CLAUDE.md/manifests/lockfiles/
   Docker/CI/Makefile/.env.example/migrations/docs; trace main modules,
   models, endpoints, tests via imports and search; read git history; detect
   implicit conventions; adapt scope to project type; mark inapplicable
   sections N/A. Phase 1 Generation: write five files (repo root by default):
   `PROJECT_BLUEPRINT.md` (executive summary → scalability, Mermaid diagrams),
   `PROJECT_CONTEXT.json` (valid JSON, fixed top-level keys: metadata,
   architecture, technologies, modules, entities, apis, workflows,
   business_rules, dependencies, coding_conventions, deployment, roadmap,
   known_limitations, technical_debt, engineering_decisions),
   `PROJECT_REBUILD_PROMPT.md` (directly reusable master prompt),
   `DECISION_LOG.md` (ADR style: Decision/Motivation/Alternatives/Trade-offs/
   Consequences), `DEVELOPMENT_STATE.md` (done/remaining/bugs/debt/risks).
   Includes a 21-point analysis checklist (product, architecture, repo org,
   modules, data model, APIs, workflows, business rules as IF/THEN/ELSE,
   patterns, decisions, dependencies, config, security, performance,
   observability, testing, standards, debt, roadmap, reconstruction guide,
   dense LLM summary). Rigor rules: label OBSERVED vs INFERRED, never dump
   large source, never invent, validate the JSON, consistency pass across the
   five files.

4. **`export_project`** — byte-identical body to project-knowledge-exporter
   (plus a blockquote right after the H1 noting it is the `/export_project`
   command form; if both installed, treat as one skill). Frontmatter name
   `export_project` (underscore — verified accepted by Claude Code), its own
   description/when_to_use mentioning the /export_project command. Wrapped by
   plugin **`export-project`** (hyphenated).

## Manifests

- `plugin.json` per plugin: `$schema` (claude-code-plugin-manifest.json),
  hyphenated `name`, `displayName`, `version 1.0.0`, `description`,
  `author {name: kalandengit}`, `repository:
  "https://github.com/kalandengit/claude-skills"`, `license: MIT`, `keywords`.
- `marketplace.json` (both): `$schema` (claude-code-marketplace.json), `name:
  kalandengit-skills`, `owner {name, url}`, `metadata.description`, `plugins[]`
  with relative `source` + `description`.

## Installer scripts (recreate the pattern)

`scripts/install-<plugin>.sh`: bash, `set -euo pipefail`; env config
`BRANCH` (default `add-<plugin>-skill`), `COMMIT=0/1`, `PUSH=0/1` (PUSH implies
COMMIT), newer ones also `RAW_URL` (default: raw.githubusercontent.com path to
`skills/<skill>/SKILL.md` on main). Behavior: resolve git top-level (fallback
cwd); write `.claude/skills/<skill>/SKILL.md` (older scripts embed content as
quoted heredoc; newer fetch via curl); insert or update a managed block in
`CLAUDE.md` between `<!-- BEGIN <skill> (managed) -->` / `<!-- END ... -->`
markers (create file with `# Project Instructions for Claude Code` header if
absent; awk-based in-place block replacement if markers present; append
otherwise); optional `git checkout -B $BRANCH`, add only the two files, commit
`Add/update <skill> Claude Code skill`, optional `git push -u origin $BRANCH`.
Idempotent on re-run.

`scripts/publish-claude-skills.sh <remote-url>`: validates
`claude-skills/.claude-plugin/marketplace.json` exists, copies the bundle to a
mktemp dir, `git init` + branch `main`, single commit, force-pushes to the
given remote (which must be a pre-created empty repo).

## CLAUDE.md

Header `# Project Instructions for Claude Code`, then one `## Skill: <name>`
section per skill stating: the skill ships at `.claude/skills/<name>/`, is
auto-discovered (including web), a 1-paragraph behavioral summary, and "Invoke
it explicitly with `/<command>`". planning-first, project-knowledge-exporter,
and export_project sections are wrapped in the managed BEGIN/END markers.

## Conventions and constraints

- Every non-initial commit to `main` goes through a PR from a `claude/*` or
  `add-*` feature branch.
- Before committing: `python3 -c "import json; json.load(...)"` every changed
  JSON, `bash -n` every changed script, `diff` the three copies of each
  SKILL.md (must be identical; `.claude/skills/` is canonical — the alias
  skill's copies are identical to *each other*, not to the exporter's).
- When adding a skill, update all 6 locations + CLAUDE.md +
  `claude-skills/README.md` (table, install commands, layout tree).
- Skill names lowercase; prefer hyphens; underscores allowed (verify discovery
  empirically). Plugin names always hyphenated.

## Known open items (preserve or fix deliberately)

- Root `LICENSE` is GPLv3 while everything else claims MIT — resolve to one.
- `kalandengit/claude-skills` standalone repo referenced but not yet published.
- Root `README.md` is a placeholder.
- No CI; consider adding a copy-sync + JSON-validity check.
