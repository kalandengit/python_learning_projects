#!/usr/bin/env bash
#
# install-planning-first.sh
# -------------------------
# Drop this file into the root of any repo (or run it from anywhere inside one)
# and execute it to install/update the `planning-first` Claude Code skill:
#
#   1. Writes  .claude/skills/planning-first/SKILL.md
#   2. Adds a marked "planning-first" section to CLAUDE.md (creating it if
#      absent, updating the section in place on re-runs, never touching the rest)
#   3. Optionally commits on a branch and pushes.
#
# Safe to run repeatedly. Requires: bash, git (only if committing/pushing).
#
# Usage:
#   ./install-planning-first.sh                 # install files only
#   COMMIT=1 ./install-planning-first.sh        # + commit on a branch
#   COMMIT=1 PUSH=1 ./install-planning-first.sh # + push the branch
#
set -euo pipefail

# ---- config (override via environment) --------------------------------------
BRANCH="${BRANCH:-add-planning-first-skill}"
COMMIT="${COMMIT:-0}"   # 1 = git add + commit on a new branch
PUSH="${PUSH:-0}"       # 1 = git push -u origin <branch> (implies COMMIT)
# -----------------------------------------------------------------------------

# Resolve the repo/working root: prefer the git top-level, else current dir.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(pwd)"
fi
cd "$ROOT"

SKILL_DIR=".claude/skills/planning-first"
SKILL_FILE="$SKILL_DIR/SKILL.md"
CLAUDE_FILE="CLAUDE.md"
BEGIN="<!-- BEGIN planning-first (managed) -->"
END="<!-- END planning-first (managed) -->"

echo ">> Target repo root: $ROOT"

# 1) Write the skill file --------------------------------------------------------
mkdir -p "$SKILL_DIR"
cat > "$SKILL_FILE" <<'SKILL_EOF'
---
name: planning-first
description: Force Claude à toujours commencer par une phase d'analyse et de planification détaillée avant toute implémentation. Use when the user requests a project, feature, architecture, automation, application, script, or system and you should analyze requirements, propose an architecture, and get explicit approval before writing any code or files.
version: 1.0.0
author: OpenAI
---

# Planning First Skill

## Purpose

This skill enforces a strict engineering workflow.

Claude must NEVER immediately produce code, files, implementations, or long answers when the user requests a project, feature, architecture, automation, application, script, or system.

Instead, Claude must first understand the request, analyze it, produce a detailed implementation plan, and wait for explicit user approval before continuing.

---

# Mandatory Workflow

For every significant technical request, Claude MUST follow these phases.

## Phase 1 — Requirement Analysis

First identify:

- the objective
- the expected outcome
- functional requirements
- non-functional requirements
- assumptions
- missing information
- possible risks
- technical constraints

If information is missing, ask questions before continuing.

---

## Phase 2 — Architecture Proposal

Describe the proposed solution.

Include when appropriate:

- architecture
- technologies
- framework choices
- libraries
- project organization
- deployment strategy
- security considerations
- scalability
- maintainability

Explain WHY each decision is made.

---

## Phase 3 — Detailed Execution Plan

Produce a numbered implementation roadmap.

Example:

1. Analyze requirements
2. Design architecture
3. Create project structure
4. Configure tooling
5. Implement backend
6. Implement frontend
7. Create database
8. Write tests
9. Write documentation
10. Deployment

Each step should contain:

- objectives
- expected deliverables
- dependencies
- estimated complexity

---

## Phase 4 — Files Preview

Before generating any files, present the complete list.

Example:

```
backend/
    app.py
    config.py
    routes.py

frontend/
    package.json
    src/
        App.tsx

docker-compose.yml
README.md
```

Explain the purpose of every file.

Do NOT generate them yet.

---

## Phase 5 — Validation

STOP.

Ask the user:

> Do you approve this architecture and implementation plan?

Do not continue until the user explicitly answers with something equivalent to:

- Yes
- Approved
- Continue
- Proceed
- Go ahead

---

## Phase 6 — Implementation

Only after approval:

Generate the project incrementally.

Never generate everything at once.

Proceed in logical stages.

Example:

Stage 1
- folder structure

(wait if appropriate)

Stage 2
- configuration

Stage 3
- backend

Stage 4
- frontend

Stage 5
- tests

Stage 6
- documentation

---

# During Implementation

For every generated file:

Provide:

- filename
- purpose
- dependencies
- explanation

Avoid dumping dozens of files in one response.

---

# Modification Requests

If the user changes requirements during development:

Return to the planning phase.

Update:

- architecture
- roadmap
- impacted files

Request approval again.

---

# Large Projects

For projects larger than approximately ten files:

Split implementation into milestones.

Example:

Milestone 1
Project initialization

Milestone 2
Core backend

Milestone 3
Authentication

Milestone 4
Frontend

Milestone 5
Testing

Milestone 6
Deployment

Each milestone requires user validation before proceeding.

---

# Forbidden Behaviors

Never:

- immediately write hundreds of lines of code
- generate an entire project in one response
- invent requirements
- skip planning
- skip architecture
- skip validation
- create files before approval

---

# Communication Style

Be methodical.

Think like:

- a software architect
- a senior consultant
- a technical lead

Prioritize:

- clarity
- planning
- maintainability
- scalability
- security

The implementation should always be driven by an approved plan.
SKILL_EOF
echo ">> Wrote $SKILL_FILE"

# 2) Add/update the managed CLAUDE.md section -----------------------------------
read -r -d '' BLOCK <<BLOCK_EOF || true
$BEGIN
## Skill: planning-first

This repository ships the **planning-first** Claude Code skill at
\`.claude/skills/planning-first/\`. Claude Code discovers it automatically in
any session opened on this repo (including Claude Code on the web, where personal
\`~/.claude\` skills are not available).

When working in this project, apply that skill for any significant technical
request: do NOT jump straight to code. First analyze requirements, propose an
architecture (explaining the reasoning), produce a numbered execution plan,
preview the files to be created, and STOP for explicit user approval before
generating anything. Implement incrementally after approval, and return to the
planning phase whenever requirements change.

Invoke it explicitly with \`/planning-first\` when you want to force this lens.
$END
BLOCK_EOF

if [ ! -f "$CLAUDE_FILE" ]; then
  printf '# Project Instructions for Claude Code\n\n%s\n' "$BLOCK" > "$CLAUDE_FILE"
  echo ">> Created $CLAUDE_FILE"
elif grep -qF "$BEGIN" "$CLAUDE_FILE"; then
  # Replace the existing managed block in place, leave everything else untouched.
  awk -v b="$BEGIN" -v e="$END" -v repl="$BLOCK" '
    $0==b {print repl; skip=1; next}
    $0==e {skip=0; next}
    skip!=1 {print}
  ' "$CLAUDE_FILE" > "$CLAUDE_FILE.tmp" && mv "$CLAUDE_FILE.tmp" "$CLAUDE_FILE"
  echo ">> Updated managed section in $CLAUDE_FILE"
else
  printf '\n%s\n' "$BLOCK" >> "$CLAUDE_FILE"
  echo ">> Appended managed section to existing $CLAUDE_FILE"
fi

# 3) Optionally commit / push ---------------------------------------------------
if [ "$PUSH" = "1" ]; then COMMIT=1; fi

if [ "$COMMIT" = "1" ]; then
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "!! COMMIT requested but this is not a git repo — skipping commit." >&2
    exit 1
  fi
  git checkout -B "$BRANCH"
  git add "$SKILL_FILE" "$CLAUDE_FILE"
  if git diff --cached --quiet; then
    echo ">> No changes to commit (already up to date)."
  else
    git commit -m "Add/update planning-first Claude Code skill"
    echo ">> Committed on branch $BRANCH"
  fi
  if [ "$PUSH" = "1" ]; then
    git push -u origin "$BRANCH"
    echo ">> Pushed $BRANCH. Open a PR on GitHub to merge."
  else
    echo ">> To publish: git push -u origin $BRANCH   (then open a PR)"
  fi
else
  echo ">> Files installed. Review, then commit/push when ready."
fi

echo ">> Done."
