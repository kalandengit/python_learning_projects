# Master_IT_Specialist_SKILL_For_All_LLM

A single, **model-agnostic** skill that merges three lenses into one:

| Merged skill | Contribution |
| ------------ | ------------ |
| **planning-first** | Analyze → propose architecture → plan → **get approval before building**. |
| **it-prompt-specialist** | Senior multidisciplinary IT expert (software, cloud, security, AI/ML, data, UX/UI, networking, embedded, game dev, PM). |
| **reverse-engineering** | Lawful, authorized reverse-engineering and binary-analysis specialist. |

The result is one "master IT specialist" that plans before it builds, covers
virtually all of IT, and can reverse-engineer binaries within a lawful,
authorized scope — with the same behavior in **any LLM**.

## Files

| File | Purpose |
| ---- | ------- |
| `PROMPT.md` | The portable system prompt with copy markers + per-platform usage recipes. |
| `prompt.txt` | The prompt with markers stripped — paste-ready. *(generated)* |
| `ollama/Modelfile` | Ready-to-build local model wrapper. *(generated)* |
| `SKILL.md` | Claude Code skill form (frontmatter + instructions). |

`prompt.txt` and `ollama/Modelfile` are generated from `PROMPT.md`'s markers by
`scripts/build-portable-prompts.sh`, so they never drift.

## Use with any LLM

- **Raw API (any provider)** — pass the prompt as the `system` field (Anthropic
  `system`, OpenAI `system` message, Gemini `system_instruction`, or any
  OpenAI-compatible endpoint).
- **ChatGPT** — a Custom GPT (Configure → Instructions) or custom instructions.
- **Google Gemini** — a Gem.
- **Claude** — a Project's custom instructions, or use `SKILL.md` as a Claude Code
  skill.
- **Mistral / Le Chat** — system prompt / agent instructions.
- **Ollama** — `ollama create master-it-specialist -f ollama/Modelfile`.
- **LM Studio / llama.cpp / text-generation-webui** — system message / `-p` field.

For the cleanest result, use `prompt.txt`, or copy only the text between the
`BEGIN PORTABLE PROMPT` / `END PORTABLE PROMPT` markers in `PROMPT.md`.

## Note on how it behaves

The plan-first ceremony (analyze → architecture → plan → approval) applies to
**build / implementation** requests. Quick questions, direct answers, code review,
and analysis are answered directly. Reverse-engineering assistance is limited to
**lawful, authorized** work; when intent is unclear, the model asks.

## License

MIT
