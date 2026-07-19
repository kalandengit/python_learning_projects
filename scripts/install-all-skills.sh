#!/usr/bin/env bash
#
# install-all-skills.sh
# ---------------------
# Installs every skill in this repo into your PERSONAL Claude Code skills
# directory (~/.claude/skills), so they are available in ALL your local
# Claude Code sessions and projects — not just this repo.
#
# Skills installed:
#   - it-prompt-specialist   (/it-prompt-specialist)
#   - planning-first         (/planning-first)
#   - export_project         (/export_project)
#
# Source of the SKILL.md files:
#   - If run from inside this repo, the local skills/<name>/SKILL.md is used.
#   - Otherwise each file is fetched from GitHub (RAW_BASE, main by default),
#     so you can run this script standalone from anywhere:
#       curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/scripts/install-all-skills.sh | bash
#
# Idempotent: re-running overwrites the installed copies with the latest.
# Requires: bash, and curl only when fetching remotely.
#
# Usage:
#   ./scripts/install-all-skills.sh                 # install into ~/.claude/skills
#   DEST=/path/to/project/.claude/skills ./scripts/install-all-skills.sh
#   RAW_BASE=https://raw.githubusercontent.com/<you>/<repo>/<branch> ./scripts/install-all-skills.sh
#
set -euo pipefail

# ---- config (override via environment) --------------------------------------
DEST="${DEST:-$HOME/.claude/skills}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/kalandengit/python_learning_projects/main}"
SKILLS=(
  it-prompt-specialist
  planning-first
  export_project
)
# -----------------------------------------------------------------------------

# Locate a local copy of the repo's skills/ dir, if we're running inside it.
LOCAL_SKILLS_DIR=""
if command -v git >/dev/null 2>&1 && git rev-parse --show-toplevel >/dev/null 2>&1; then
  _root="$(git rev-parse --show-toplevel)"
  [ -d "$_root/skills" ] && LOCAL_SKILLS_DIR="$_root/skills"
fi
# Also handle "bash scripts/install-all-skills.sh" without git.
if [ -z "$LOCAL_SKILLS_DIR" ]; then
  _here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd)"
  [ -d "$_here/../skills" ] && LOCAL_SKILLS_DIR="$(cd "$_here/.." && pwd)/skills"
fi

echo ">> Installing ${#SKILLS[@]} skill(s) into: $DEST"
if [ -n "$LOCAL_SKILLS_DIR" ]; then
  echo ">> Source: local repo ($LOCAL_SKILLS_DIR)"
else
  echo ">> Source: remote ($RAW_BASE/skills/<name>/SKILL.md)"
fi

installed=0
for name in "${SKILLS[@]}"; do
  target_dir="$DEST/$name"
  target_file="$target_dir/SKILL.md"
  mkdir -p "$target_dir"

  if [ -n "$LOCAL_SKILLS_DIR" ] && [ -f "$LOCAL_SKILLS_DIR/$name/SKILL.md" ]; then
    cp "$LOCAL_SKILLS_DIR/$name/SKILL.md" "$target_file"
  else
    if ! command -v curl >/dev/null 2>&1; then
      echo "!! curl is required to fetch '$name' remotely but is not installed." >&2
      exit 1
    fi
    curl -fsSL "$RAW_BASE/skills/$name/SKILL.md" -o "$target_file"
  fi
  echo "   + $name -> $target_file"
  installed=$((installed + 1))
done

echo ">> Done. Installed $installed skill(s)."
echo
echo "These now load in every LOCAL Claude Code session. Verify with /help or by"
echo "invoking one, e.g.  /export_project"
echo
echo "Note: personal ~/.claude/skills do NOT load in Claude Code on the web."
echo "For web + every project, add the plugin marketplace instead (run inside Claude Code):"
echo "    /plugin marketplace add kalandengit/python_learning_projects"
echo "    /plugin install it-prompt-specialist@kalandengit-skills"
echo "    /plugin install planning-first@kalandengit-skills"
echo "    /plugin install export-project@kalandengit-skills"
