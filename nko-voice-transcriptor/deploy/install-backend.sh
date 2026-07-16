#!/usr/bin/env bash
# N'Ko Voice Transcriptor 1.8.0 — copy/paste Ubuntu backend installer.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kalandengit/python_learning_projects.git}"
REPO_REF="${REPO_REF:-main}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/kalandengit/python_learning_projects/${REPO_REF}}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash install-backend.sh" >&2
  exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location \
  "${RAW_BASE}/nko-voice-transcriptor/deploy/deploy-ubuntu.sh" -o "$tmp"

# Pass the selected repository/ref to the audited deployment script.
REPO_URL="$REPO_URL" REPO_REF="$REPO_REF" bash "$tmp"
