#!/usr/bin/env bash
#
# N'Ko Voice Transcriptor — backend UPDATE script for Ubuntu LTS.
#
# Companion to deploy-ubuntu.sh: updates an existing installation to the
# latest code without touching Nginx, PostgreSQL, TLS, or the secrets in
# /etc/nko-transcriptor.env. Keeps a timestamped backup of the previous code
# and rolls back automatically if the service fails its health check.
#
# COPY-PASTE (run as root or with sudo):
#
#   sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/nko-voice-transcriptor-b3u9zg/nko-voice-transcriptor/deploy/update-ubuntu.sh)"
#
# Options (env vars): REPO_REF=main  APP_HOME=/opt/nko-voice-transcriptor
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kalandengit/python_learning_projects.git}"
REPO_REF="${REPO_REF:-claude/nko-voice-transcriptor-b3u9zg}"
APP_SUBDIR="${APP_SUBDIR:-nko-voice-transcriptor}"
APP_HOME="${APP_HOME:-/opt/nko-voice-transcriptor}"
APP_USER="${APP_USER:-nko}"
APP_PORT="${APP_PORT:-8000}"
SERVICE_NAME="${SERVICE_NAME:-nko-transcriptor}"

log()  { printf '\033[1;32m>> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31mXX %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo)."
[ -d "$APP_HOME/app" ] || die "No installation at $APP_HOME — run deploy-ubuntu.sh first."
systemctl cat "$SERVICE_NAME" >/dev/null 2>&1 || die "Service $SERVICE_NAME not found — run deploy-ubuntu.sh first."

OLD_VERSION="$(grep -oP '__version__ = "\K[^"]+' "$APP_HOME/app/__init__.py" 2>/dev/null || echo '?')"

# ---- 1. Fetch the requested ref --------------------------------------------
log "Fetching ${REPO_REF}..."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$TMP/repo" 2>/dev/null \
  || die "Could not clone ${REPO_REF} from ${REPO_URL}."
[ -d "$TMP/repo/$APP_SUBDIR/app" ] || die "App not found in the fetched ref."
NEW_VERSION="$(grep -oP '__version__ = "\K[^"]+' "$TMP/repo/$APP_SUBDIR/app/__init__.py" || echo '?')"

# ---- 2. Backup current code -------------------------------------------------
BACKUP="${APP_HOME}.backup-$(date +%Y%m%d-%H%M%S)"
log "Backing up current code (${OLD_VERSION}) to ${BACKUP}..."
mkdir -p "$BACKUP"
# Code only — leave the venv and any SQLite DB in place.
for item in app pyproject.toml requirements.txt requirements-dev.txt; do
  [ -e "$APP_HOME/$item" ] && cp -a "$APP_HOME/$item" "$BACKUP/" || true
done

# ---- 3. Sync new code + dependencies ---------------------------------------
log "Updating code ${OLD_VERSION} -> ${NEW_VERSION}..."
cp -a "$TMP/repo/$APP_SUBDIR/." "$APP_HOME/"
"$APP_HOME/.venv/bin/pip" install --quiet --upgrade -r "$APP_HOME/requirements.txt"
chown -R "$APP_USER":"$APP_USER" "$APP_HOME"

# ---- 4. Restart + health check (rollback on failure) ------------------------
log "Restarting ${SERVICE_NAME}..."
systemctl restart "$SERVICE_NAME"
HEALTHY=0
for _ in $(seq 1 20); do
  curl -fsS "http://127.0.0.1:${APP_PORT}/api/health" >/dev/null 2>&1 && { HEALTHY=1; break; }
  sleep 1
done

if [ "$HEALTHY" = "1" ]; then
  log "Update OK: $(curl -fsS "http://127.0.0.1:${APP_PORT}/api/health")"
  log "Previous code kept at ${BACKUP} (delete when satisfied)."
else
  warn "Health check FAILED — rolling back to ${OLD_VERSION}..."
  for item in app pyproject.toml requirements.txt requirements-dev.txt; do
    [ -e "$BACKUP/$item" ] && rm -rf "${APP_HOME:?}/$item" && cp -a "$BACKUP/$item" "$APP_HOME/"
  done
  "$APP_HOME/.venv/bin/pip" install --quiet -r "$APP_HOME/requirements.txt" || true
  chown -R "$APP_USER":"$APP_USER" "$APP_HOME"
  systemctl restart "$SERVICE_NAME" || true
  die "Rolled back. Inspect: journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
fi
