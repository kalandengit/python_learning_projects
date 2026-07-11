# project-knowledge-exporter

A [Claude Code](https://claude.com/claude-code) Skill that turns a live software
project into a **durable, LLM-portable Project Knowledge Package** — so the
project can be understood, maintained, extended, and even **reconstructed from
scratch** if the original repository, git history, and conversations are lost.

## What it does

The skill drives Claude through a two-phase workflow:

1. **Discovery** — Claude actually reads the repository (tree, `README`/`CLAUDE.md`,
   manifests and lockfiles, Docker/CI config, source modules, models, APIs,
   tests, and git history) instead of relying on pasted snippets or memory.
2. **Generation** — Claude writes five knowledge files, grounded in what it found:

   | File | Purpose |
   | ---- | ------- |
   | `PROJECT_BLUEPRINT.md` | Full functional + technical blueprint, with Mermaid diagrams for architecture, sequences, and ER models. |
   | `PROJECT_CONTEXT.json` | Structured, valid-JSON twin of the blueprint, optimized for another LLM to ingest. |
   | `PROJECT_REBUILD_PROMPT.md` | A ready-to-use Master Prompt another LLM can run to rebuild the whole project. |
   | `DECISION_LOG.md` | Major engineering decisions in ADR style (decision, motivation, alternatives, trade-offs, consequences). |
   | `DEVELOPMENT_STATE.md` | Current state: done, remaining, known bugs, tech debt, missing features, risks. |

It captures **intent, architecture, interfaces, data flow, and rationale** —
without dumping large blocks of source code — and clearly labels **observed
facts vs. reasonable inferences**.

## Why use it

- **Handoffs** — onboard another team or LLM with a single, self-contained package.
- **Preservation** — keep the engineering memory of a project even if the repo disappears.
- **Reconstruction** — regenerate the project from the rebuild prompt with minimal information loss.

## Installation

### Personal skill (available in all your projects)

```bash
mkdir -p ~/.claude/skills/project-knowledge-exporter
curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/project-knowledge-exporter/SKILL.md \
  -o ~/.claude/skills/project-knowledge-exporter/SKILL.md
```

### Project skill (single project)

Place `SKILL.md` at `.claude/skills/project-knowledge-exporter/SKILL.md` in the
project root, or run the installer:

```bash
COMMIT=1 PUSH=1 ./scripts/install-project-knowledge-exporter.sh
```

### Plugin marketplace (every project, including Claude Code on the web)

```
/plugin marketplace add kalandengit/python_learning_projects
/plugin install project-knowledge-exporter@kalandengit-skills
```

## Usage

Invoke explicitly:

```
/project-knowledge-exporter Export a full knowledge package for this repo
```

Or just ask Claude to "document this whole project so another LLM could rebuild
it" and the skill activates automatically.

## License

MIT
