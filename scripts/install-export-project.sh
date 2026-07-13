#!/usr/bin/env bash
#
# install-export-project.sh
# -------------------------------------
# Run this from anywhere inside a git repo (or drop it into a repo root) to
# install/update the `export_project` Claude Code skill:
#
#   1. Writes  .claude/skills/export_project/SKILL.md
#   2. Adds a marked "export_project" section to CLAUDE.md (creating
#      it if absent, updating the section in place on re-runs, never touching
#      the rest).
#   3. Optionally commits on a branch and pushes.
#
# The SKILL.md is fetched from this repo's raw content so there is a single
# source of truth. Override RAW_URL to install from a fork/branch.
#
# Safe to run repeatedly. Requires: bash, curl, git (only if committing/pushing).
#
# Usage:
#   ./install-export-project.sh                 # install files only
#   COMMIT=1 ./install-export-project.sh        # + commit on a branch
#   COMMIT=1 PUSH=1 ./install-export-project.sh # + push the branch
#
set -euo pipefail

# ---- config (override via environment) --------------------------------------
BRANCH="${BRANCH:-add-export-project-skill}"
COMMIT="${COMMIT:-0}"   # 1 = git add + commit on a new branch
PUSH="${PUSH:-0}"       # 1 = git push -u origin <branch> (implies COMMIT)
RAW_URL="${RAW_URL:-https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/export_project/SKILL.md}"
# -----------------------------------------------------------------------------

# Resolve the repo/working root: prefer the git top-level, else current dir.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(pwd)"
fi
cd "$ROOT"

SKILL_DIR=".claude/skills/export_project"
SKILL_FILE="$SKILL_DIR/SKILL.md"
CLAUDE_FILE="CLAUDE.md"
BEGIN="<!-- BEGIN export_project (managed) -->"
END="<!-- END export_project (managed) -->"

echo ">> Target repo root: $ROOT"

# 1) Write the skill file --------------------------------------------------------
mkdir -p "$SKILL_DIR"
echo ">> Fetching SKILL.md from $RAW_URL"
curl -fsSL "$RAW_URL" -o "$SKILL_FILE"
echo ">> Wrote $SKILL_FILE"

# 2) Add/update the managed CLAUDE.md section -----------------------------------
read -r -d '' BLOCK <<BLOCK_EOF || true
$BEGIN
## Skill: export_project

This repository ships the **export_project** Claude Code skill at
\`.claude/skills/export_project/\`, invoked with \`/export_project\`. Claude Code
discovers it automatically in any session opened on this repo (including Claude
Code on the web, where personal \`~/.claude\` skills are not available).

When the user runs \`/export_project\` or asks to export/snapshot/hand off the
project, apply that skill: first **investigate the repo** (tree,
README/CLAUDE.md, manifests, Docker/CI, source, models, APIs, tests, git
history), then generate the five knowledge files — \`PROJECT_BLUEPRINT.md\`,
\`PROJECT_CONTEXT.json\`, \`PROJECT_REBUILD_PROMPT.md\`, \`DECISION_LOG.md\`, and
\`DEVELOPMENT_STATE.md\` — grounded in what you found, labeling observed facts
vs. inferences and avoiding large source dumps.
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
    git commit -m "Add/update export_project Claude Code skill"
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
