#!/usr/bin/env bash
#
# publish-claude-skills.sh
# ------------------------
# Publishes the ready-made Claude Code skills marketplace bundle
# (claude-skills/) to a GitHub repository as its own standalone repo.
#
# Prereqbuisite: create an EMPTY repo on GitHub first (no README), e.g.
#   https://github.com/new  ->  name: claude-skills  ->  Public  ->  Create
# Do NOT initialize it with a README/license (the bundle already has both).
#
# Usage:
#   ./scripts/publish-claude-skills.sh git@github.com:kalandengit/claude-skills.git
#   ./scripts/publish-claude-skills.sh https://github.com/kalandengit/claude-skills.git
#
# This force-updates the remote 'main'. It is destructive, so it refuses to push
# unless CONFIRM_FORCE_PUSH=1 is set, prints the resolved remote for review, and
# uses --force-with-lease:
#   CONFIRM_FORCE_PUSH=1 ./scripts/publish-claude-skills.sh <git-remote-url>
set -euo pipefail

REMOTE="${1:-}"
if [ -z "$REMOTE" ]; then
  echo "Usage: $0 <git-remote-url>" >&2
  echo "  e.g. $0 https://github.com/kalandengit/claude-skills.git" >&2
  exit 2
fi

# Resolve repo root so the script works from anywhere.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(pwd)"
fi
BUNDLE="$ROOT/claude-skills"

if [ ! -f "$BUNDLE/.claude-plugin/marketplace.json" ]; then
  echo "!! Bundle not found at $BUNDLE (missing .claude-plugin/marketplace.json)" >&2
  exit 1
fi

# Publish the bundle from a temp clone so we never touch this repo's git state.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp -R "$BUNDLE/." "$WORK/"

cd "$WORK"
git init -q
git checkout -q -b main
git add -A
git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name || echo kalandengit)}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-$(git config user.email || echo kalan.kalandeh@gmail.com)}" \
    commit -q -m "Publish claude-skills marketplace (planning-first, it-prompt-specialist, reverse-engineering)"
git remote add origin "$REMOTE"

# Force-updating a remote 'main' is destructive: require explicit opt-in and
# show the resolved remote so a mistyped argument cannot silently overwrite the
# wrong repository. Use --force-with-lease so we never clobber unseen commits.
RESOLVED="$(git remote get-url origin)"
echo ">> Target remote resolves to: $RESOLVED (branch main)"
if [ "${CONFIRM_FORCE_PUSH:-0}" != "1" ]; then
    echo "!! Refusing to force-push. This overwrites 'main' on the target remote." >&2
    echo "   Re-run with CONFIRM_FORCE_PUSH=1 once you've verified the remote above." >&2
    echo "   Ensure branch protection is configured on the destination repository." >&2
    exit 1
fi
echo ">> Pushing bundle to $RESOLVED (branch main)..."
git push -u --force-with-lease origin main
echo ">> Done. In Claude Code:  /plugin marketplace add kalandengit/claude-skills"
