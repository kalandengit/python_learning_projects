# planning-first

A [Claude Code](https://claude.com/claude-code) Skill that forces Claude to
**always start with analysis and detailed planning before any implementation**.

Instead of jumping straight to code, Claude first understands the request,
analyzes requirements, proposes an architecture, produces a step-by-step
execution plan, previews the files it will create, and then **waits for your
explicit approval** before writing anything.

## What it does

For every significant technical request (a project, feature, architecture,
automation, application, script, or system), Claude follows a strict workflow:

1. **Requirement analysis** — objective, functional/non-functional requirements,
   assumptions, missing information, risks, and constraints (asks questions when
   information is missing).
2. **Architecture proposal** — technologies, framework/library choices, project
   organization, deployment, security, scalability, maintainability — with the
   reasoning behind each decision.
3. **Detailed execution plan** — a numbered roadmap with objectives,
   deliverables, dependencies, and estimated complexity per step.
4. **Files preview** — the complete list of files to be created, with the
   purpose of each — but nothing is generated yet.
5. **Validation** — Claude stops and asks for explicit approval.
6. **Implementation** — only after approval, generated incrementally in logical
   stages (and split into milestones for larger projects).

If requirements change mid-development, Claude returns to the planning phase and
requests approval again.

## Use with any LLM (portable prompt)

This skill also ships a **model-agnostic** version: [`PROMPT.md`](./PROMPT.md), with
extract-ready [`prompt.txt`](./prompt.txt) (markers stripped) and an
[`ollama/Modelfile`](./ollama/Modelfile) for local models. Drop it into ChatGPT
(Custom GPT / custom instructions), Google Gemini (Gems), Claude (Projects),
Mistral, or pass it as the `system` field of any raw API call. The extract-ready
files are generated from `PROMPT.md` by `scripts/build-portable-prompts.sh`, so
they never drift.

## Installation (Claude Code)

### Personal skill (available in all your projects)

```bash
mkdir -p ~/.claude/skills/planning-first
curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/planning-first/SKILL.md \
  -o ~/.claude/skills/planning-first/SKILL.md
```

### Project skill (single project)

Place `SKILL.md` at `.claude/skills/planning-first/SKILL.md` in the project root,
or run the installer:

```bash
COMMIT=1 PUSH=1 ./scripts/install-planning-first.sh
```

## Usage

Invoke explicitly:

```
/planning-first Build me a REST API for a todo application
```

Or just describe a project — Claude applies the skill automatically and starts
with a plan instead of code.

## License

MIT
