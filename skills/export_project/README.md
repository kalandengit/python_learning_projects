# export_project

The **`/export_project`** command for [Claude Code](https://claude.com/claude-code)
and Claude chats.

Running it turns the current project into a durable, LLM-portable **Project
Knowledge Package**: Claude first investigates the repository (tree,
README/CLAUDE.md, manifests, Docker/CI, source, models, APIs, tests, git
history), then writes five knowledge files grounded in what it found:

| File | Purpose |
| ---- | ------- |
| `PROJECT_BLUEPRINT.md` | Full functional + technical blueprint with Mermaid diagrams |
| `PROJECT_CONTEXT.json` | Valid-JSON structured twin, optimized for LLM ingestion |
| `PROJECT_REBUILD_PROMPT.md` | Ready-to-run Master Prompt to rebuild the project |
| `DECISION_LOG.md` | Major engineering decisions in ADR style |
| `DEVELOPMENT_STATE.md` | Completed / remaining work, bugs, tech debt, risks |

## Install — all Claude Code projects (recommended)

Via the plugin marketplace (works locally **and** on Claude Code on the web):

```
/plugin marketplace add kalandengit/python_learning_projects
/plugin install export-project@kalandengit-skills
```

Then run `/export_project` in any project.

## Install — personal skill (`~/.claude`, local projects)

```bash
mkdir -p ~/.claude/skills/export_project
curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/export_project/SKILL.md \
  -o ~/.claude/skills/export_project/SKILL.md
```

## Install — single project

```bash
COMMIT=1 PUSH=1 ./scripts/install-export-project.sh
```

Or copy `SKILL.md` to `.claude/skills/export_project/SKILL.md` in the project.

## Install — claude.ai chats (web / desktop / mobile)

Claude chats accept custom skills as a zip upload:

```bash
cd skills && zip -r export_project.zip export_project/SKILL.md
```

Then in claude.ai: **Settings → Capabilities → Skills → Upload skill** and pick
`export_project.zip`. The skill activates in chats when you ask Claude to
export/snapshot a project (attach or connect the project files so it has
something to analyze).

## Usage

```
/export_project
/export_project Export a knowledge package into knowledge-export/
```

## License

MIT
