# claude-skills

A [Claude Code](https://claude.com/claude-code) **plugin marketplace** hosting
reusable skills by [@kalandengit](https://github.com/kalandengit).

Install once and the skills are available in **every** Claude Code project —
including Claude Code on the web, where personal `~/.claude` skills don't load.

## Skills

| Plugin | What it does |
| ------ | ------------ |
| **planning-first** | Forces a plan-first workflow — analyze requirements, propose an architecture, present an execution plan + files preview, and get explicit approval **before** writing any code or files. |
| **it-prompt-specialist** | A senior multidisciplinary IT expert lens across software, cloud, security, AI/ML, networking, embedded, game dev, and project management. |
| **project-knowledge-exporter** | Analyzes an entire project and generates a durable, LLM-portable knowledge package — blueprint, structured context JSON, rebuild prompt, decision log, and development-state report — for handoff and reconstruction. |

## Install (plugin marketplace — recommended)

In any Claude Code session:

```
/plugin marketplace add kalandengit/claude-skills
/plugin install planning-first@kalandengit-skills
/plugin install it-prompt-specialist@kalandengit-skills
/plugin install project-knowledge-exporter@kalandengit-skills
```

Refresh later with `/plugin marketplace update`. Invoke a skill explicitly with
`/planning-first`, `/it-prompt-specialist`, or `/project-knowledge-exporter`, or
just describe a task and Claude activates the relevant skill automatically.

## Install (single skill into ~/.claude — local projects only)

```bash
mkdir -p ~/.claude/skills/planning-first
curl -fsSL https://raw.githubusercontent.com/kalandengit/claude-skills/main/plugins/planning-first/skills/planning-first/SKILL.md \
  -o ~/.claude/skills/planning-first/SKILL.md
```

## Layout

```
.claude-plugin/
    marketplace.json                      # marketplace catalog
plugins/
    planning-first/
        .claude-plugin/plugin.json        # plugin manifest
        skills/planning-first/SKILL.md     # the skill
    it-prompt-specialist/
        .claude-plugin/plugin.json
        skills/it-prompt-specialist/SKILL.md
    project-knowledge-exporter/
        .claude-plugin/plugin.json
        skills/project-knowledge-exporter/SKILL.md
```

## License

MIT
