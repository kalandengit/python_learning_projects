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
| **reverse-engineering** | A senior reverse-engineering and binary-analysis lens — static/dynamic analysis, disassembly, decompilation, malware triage, firmware, protocol reversing, and mobile RE. Scoped to lawful, authorized work. |
| **master-it-specialist-for-all-llm** | The three skills above **merged** into one model-agnostic "master IT specialist" — plan-first + full IT breadth + lawful reverse engineering. Ships a portable prompt for use in any LLM. |

## Install (plugin marketplace — recommended)

In any Claude Code session:

```
/plugin marketplace add kalandengit/claude-skills
/plugin install planning-first@kalandengit-skills
/plugin install it-prompt-specialist@kalandengit-skills
/plugin install reverse-engineering@kalandengit-skills
/plugin install master-it-specialist-for-all-llm@kalandengit-skills
```

Refresh later with `/plugin marketplace update`. Invoke a skill explicitly with
`/planning-first`, `/it-prompt-specialist`, `/reverse-engineering`, or
`/master-it-specialist-for-all-llm`, or just describe a task and Claude activates
the relevant skill automatically.

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
    reverse-engineering/
        .claude-plugin/plugin.json
        skills/reverse-engineering/SKILL.md
    master-it-specialist-for-all-llm/
        .claude-plugin/plugin.json
        skills/master-it-specialist-for-all-llm/SKILL.md
```

## License

MIT
