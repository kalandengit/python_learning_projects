# it-prompt-specialist

A [Claude Code](https://claude.com/claude-code) Skill that transforms Claude into a
**senior multidisciplinary IT expert** covering software engineering, infrastructure,
cybersecurity, cloud, AI/ML, data, UX/UI, networking, embedded systems, game
development, project management, and technical documentation.

It adapts automatically to your experience level while maintaining engineering best
practices, security, maintainability, and production-quality recommendations.

## What it does

When active, Claude answers, designs, reviews, troubleshoots, documents, and
implements solutions across virtually every area of IT, with dedicated modes for:

- **Coding** — production-ready, tested, secure, documented code with type annotations
- **Architecture** — component breakdowns, scaling/caching strategies, ASCII diagrams
- **Troubleshooting** — structured issue → cause → diagnostics → fix → prevention
- **Code review** — readability, maintainability, performance, security, testing
- **Documentation** — READMEs, API docs, ADRs, runbooks, deployment guides, changelogs
- **Security** — secure-by-default (OWASP Top 10, Zero Trust, least privilege, secrets)
- **AI/ML, DevOps, Cloud, Data, UX/UI, Networking, Embedded, Game Dev, PM**

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
mkdir -p ~/.claude/skills/it-prompt-specialist
curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/it-prompt-specialist/SKILL.md \
  -o ~/.claude/skills/it-prompt-specialist/SKILL.md
```

### Project skill (single project)

Place `SKILL.md` at `.claude/skills/it-prompt-specialist/SKILL.md` in the project root.

## Usage

Invoke explicitly:

```
/it-prompt-specialist How should I design a multi-region PostgreSQL deployment?
```

Or just ask an IT question — Claude applies the skill automatically when a request
calls for expert-level IT design, review, troubleshooting, or implementation.

## License

MIT
