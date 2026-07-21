#!/usr/bin/env bash
#
# publish-master-skill.sh
# -----------------------
# Publishes the Master_IT_Specialist_SKILL_For_All_LLM bundle
# (skills/Master_IT_Specialist_SKILL_For_All_LLM/) to a GitHub repository as its
# own standalone repo — so the bundle's files sit at the repo root.
#
# Prerequisite: create an EMPTY repo on GitHub first (no README/license), e.g.
#   https://github.com/new  ->  name: Master_IT_Specialist_SKILL_For_All_LLM
#   ->  Public  ->  Create.  Do NOT initialize it (the bundle already has a
#   README and LICENSE).
#
# Usage:
#   ./scripts/publish-master-skill.sh git@github.com:kalandengit/Master_IT_Specialist_SKILL_For_All_LLM.git
#   ./scripts/publish-master-skill.sh https://github.com/kalandengit/Master_IT_Specialist_SKILL_For_All_LLM.git
#
# Safe to re-run: it force-updates the remote 'main' with the current bundle.
set -euo pipefail

REMOTE="${1:-}"
if [ -z "$REMOTE" ]; then
  echo "Usage: $0 <git-remote-url>" >&2
  echo "  e.g. $0 https://github.com/kalandengit/Master_IT_Specialist_SKILL_For_All_LLM.git" >&2
  exit 2
fi

# Resolve repo root so the script works from anywhere.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(pwd)"
fi
BUNDLE="$ROOT/skills/Master_IT_Specialist_SKILL_For_All_LLM"

if [ ! -f "$BUNDLE/SKILL.md" ] || [ ! -f "$BUNDLE/PROMPT.md" ]; then
  echo "!! Bundle not found at $BUNDLE (missing SKILL.md / PROMPT.md)" >&2
  exit 1
fi

# Keep the extract-ready files in sync with PROMPT.md before publishing.
if [ -x "$ROOT/scripts/build-portable-prompts.sh" ]; then
  "$ROOT/scripts/build-portable-prompts.sh" >/dev/null || true
fi

# Publish from a temp clone so we never touch this repo's git state.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp -R "$BUNDLE/." "$WORK/"

cd "$WORK"
git init -q
git checkout -q -b main
git add -A
git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name || echo kalandengit)}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-$(git config user.email || echo kalan.kalandeh@gmail.com)}" \
    commit -q -m "Publish Master_IT_Specialist_SKILL_For_All_LLM (portable, model-agnostic skill)"
git remote add origin "$REMOTE"
echo ">> Pushing bundle to $REMOTE (branch main)..."
git push -u --force origin main
echo ">> Done."
echo ">> Portable prompt:  PROMPT.md / prompt.txt / ollama/Modelfile"
echo ">> Claude Code skill: SKILL.md"
