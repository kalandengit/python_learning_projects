---
name: project-knowledge-exporter
description: Reverse-engineers the currently open project into a complete, self-contained knowledge-transfer package so another LLM (Claude, ChatGPT, Gemini, DeepSeek, Cursor, Windsurf, Copilot, etc.) can reconstruct it faithfully with minimal context loss. Produces PROJECT_BLUEPRINT.md (rich narrative documentation) and PROJECT_CONTEXT.json (normalized machine-readable memory). Use whenever the user asks to export, document, snapshot, hand off, transfer, back up, summarize for an LLM, "onboard another AI to", reverse-engineer, or reconstruct a project — or mentions long-term project memory, context export, blueprint, or knowledge dump.
version: 2.0.0
license: MIT
metadata:
  role: Software Architect · Tech Lead · Knowledge Engineer
---

# Project Knowledge Exporter (Reverse Engineering Context Exporter)

## Purpose

Analyze the **entire open project** and produce a **knowledge-transfer package** that lets a different LLM — with **no access to this Git repository** — reconstruct the project with maximum fidelity.

This is **not a summary**. It is a durable, structured **representation of the project's knowledge**, meant to serve as the project's long-term memory. Both deliverables must be **self-contained**: understandable and actionable without reading the source code.

## Role

Operate as a senior **Software Architect + Tech Lead + Knowledge Engineer** specialized in LLM-oriented reverse engineering. Reason about architecture, contracts, business rules, and design decisions — not just file contents.

## When to use

Trigger on requests like: "export/document/snapshot this project", "hand this off to another AI", "make a blueprint", "context for ChatGPT/Gemini/Cursor", "long-term project memory", "reverse-engineer this repo", "generate a reconstruction prompt".

## Deliverables

Produce **two complementary, consistent files** at the project root (unless the user names a different location):

| File | Format | Audience | Purpose |
|------|--------|----------|---------|
| `PROJECT_BLUEPRINT.md` | Markdown | Humans + LLMs | Preserves reasoning, decisions, workflows, and narrative context |
| `PROJECT_CONTEXT.json` | JSON | LLMs + tooling | Normalized, parseable "structured memory" for regeneration/automation |

The `.md` carries the *why*; the `.json` carries a normalized *what* that tools and models can ingest almost directly. **They must not contradict each other.**

## Process

Work in phases. Do not fabricate — if something cannot be determined from the repo, mark it explicitly as `UNKNOWN` / `NOT PRESENT` rather than inventing it.

1. **Reconnaissance.** Map the repo: full directory tree, entry points, config/manifest files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, CI configs, `.env.example`), and READMEs/docs. Detect languages, frameworks, and project type.
2. **Deep analysis.** Read representative source across every module. Recover: architecture and layering, data models/schema/migrations, API/interface contracts, business rules and invariants, workflows, cross-cutting concerns (auth, security, caching, logging, tests), and notable design decisions. Prefer interface contracts and algorithms over copying code.
3. **Author `PROJECT_BLUEPRINT.md`.** Follow the full section structure and quality bar in
   `references/blueprint-template.md`. Cover all sections; write `N/A — not applicable to this project` where a section genuinely does not apply (e.g., no database in a CLI tool) rather than omitting it.
4. **Author `PROJECT_CONTEXT.json`.** Populate the schema in `references/context-schema.json`. It **must be syntactically valid JSON** and consistent with the `.md`. Use `null` / empty arrays for genuinely-absent data; never invent values to fill fields.
5. **Cross-check & report.** Verify the two files agree (same stack, modules, entities, rules). Validate the JSON parses. Then tell the user what was produced, list any `UNKNOWN`/assumption areas, and note where the reconstruction prompt lives (final section of the blueprint).

## Hard constraints

- **Do not paste the codebase.** Describe structure, logic, interface contracts, algorithms, conventions, and decisions. Code snippets are allowed **only** as short illustrative examples (a few lines).
- **Self-contained.** A reader with no repo access must be able to understand and rebuild the project.
- **Accuracy over completeness.** Mark unknowns explicitly. Do not guess versions, secrets, or hidden behavior.
- **Never include secrets.** Reference env-var *names* and their purpose; never copy real credential values from `.env`, configs, or history.
- **Language.** Technical terms in English; narrative/business descriptions may follow the project's or user's dominant language (default: match the user).
- **Consistency.** The `.md` and `.json` must tell the same story.

## Quality bar (self-check before finishing)

- Both files cover every required section/field; nothing silently dropped.
- `PROJECT_CONTEXT.json` is valid JSON and self-descriptive.
- A human could understand the project without reading the code.
- Another LLM could produce a plausible first working version from these files alone.
- Architecture decisions are justified; business rules are explicit and unambiguous.
- Technical debt, limitations, and roadmap are documented honestly.
- The final "Reconstruction Prompt" section is copy-paste ready for another LLM.

## Reference files

- `references/blueprint-template.md` — the complete 22-section structure, guidance, and reconstruction-prompt template for `PROJECT_BLUEPRINT.md`.
- `references/context-schema.json` — the annotated schema/skeleton for `PROJECT_CONTEXT.json`.
