#!/usr/bin/env bash
#
# N'Ko Voice Transcriptor — one-shot backend deployment for Ubuntu LTS
# (tested targets: Ubuntu 24.04 / 26.04 LTS). Idempotent: safe to re-run.
#
# It installs system packages, creates a dedicated service user, fetches the
# app, builds a virtualenv, writes a hardened .env, runs the app under systemd
# via Gunicorn+Uvicorn workers, and puts Nginx in front — optionally with
# PostgreSQL, Let's Encrypt TLS, and a UFW firewall.
#
# ---------------------------------------------------------------------------
# COPY-PASTE QUICK START (run as root or with sudo):
#
#   sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/nko-voice-transcriptor-b3u9zg/nko-voice-transcriptor/deploy/deploy-ubuntu.sh)"
#
# With a domain + HTTPS + PostgreSQL:
#
#   sudo DOMAIN=nko.example.com ENABLE_TLS=1 [email protected] USE_POSTGRES=1 \
#     bash -c "$(curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/nko-voice-transcriptor-b3u9zg/nko-voice-transcriptor/deploy/deploy-ubuntu.sh)"
#
# Or clone the repo and run it locally:
#
#   sudo ./nko-voice-transcriptor/deploy/deploy-ubuntu.sh
# ---------------------------------------------------------------------------
set -euo pipefail

# ---- Configuration (override via environment) ------------------------------
REPO_URL="${REPO_URL:-https://github.com/kalandengit/python_learning_projects.git}"
# Branch/tag to deploy. Change to "main" once the PR is merged.
REPO_REF="${REPO_REF:-claude/nko-voice-transcriptor-b3u9zg}"
# Subdirectory of the repo that holds the backend.
APP_SUBDIR="${APP_SUBDIR:-nko-voice-transcriptor}"

APP_USER="${APP_USER:-nko}"
APP_HOME="${APP_HOME:-/opt/nko-voice-transcriptor}"
APP_PORT="${APP_PORT:-8000}"            # internal port (Nginx proxies to it)
WORKERS="${WORKERS:-}"                   # blank = auto (2*CPU+1, capped)

DOMAIN="${DOMAIN:-}"                      # e.g. nko.example.com ("" = serve on IP)
ENABLE_TLS="${ENABLE_TLS:-0}"            # 1 + DOMAIN + EMAIL → Let's Encrypt
EMAIL="${EMAIL:-}"                        # for certbot registration
USE_POSTGRES="${USE_POSTGRES:-0}"       # 1 = provision local PostgreSQL
ASR_ENGINE="${ASR_ENGINE:-mock}"        # mock | mms (mms pulls ~2GB torch stack)
MMS_MODEL_ID="${MMS_MODEL_ID:-facebook/mms-1b-all}"
MODEL_VERSION="${MODEL_VERSION:-base}"
LLM_PROVIDER="${LLM_PROVIDER:-none}"    # none | openai | groq | custom
LLM_API_KEY="${LLM_API_KEY:-}"          # required when provider is enabled
LLM_MODEL="${LLM_MODEL:-}"              # blank = provider default
LLM_BASE_URL="${LLM_BASE_URL:-}"        # required for custom; OpenAI-compatible API
SETUP_FIREWALL="${SETUP_FIREWALL:-1}"   # 1 = configure UFW (OpenSSH + Nginx)

SERVICE_NAME="nko-transcriptor"
ENV_FILE="/etc/${SERVICE_NAME}.env"

# ---- Helpers ---------------------------------------------------------------
log()  { printf '\033[1;32m>> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31mXX %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Please run as root (use: sudo $0)"
command -v systemctl >/dev/null || die "systemd is required (Ubuntu Server LTS)."
[ "$LLM_PROVIDER" = "none" ] || [ -n "$LLM_API_KEY" ] || die "LLM_API_KEY is required for LLM_PROVIDER=$LLM_PROVIDER."

if [ "$ENABLE_TLS" = "1" ]; then
  [ -n "$DOMAIN" ] || die "ENABLE_TLS=1 requires DOMAIN."
  [ -n "$EMAIL" ]  || die "ENABLE_TLS=1 requires EMAIL (for Let's Encrypt)."
fi

export DEBIAN_FRONTEND=noninteractive

# ---- 1. System packages ----------------------------------------------------
log "Installing system packages..."
apt-get update -qq
PKGS=(python3 python3-venv python3-pip git nginx curl ca-certificates ufw ffmpeg)
[ "$USE_POSTGRES" = "1" ] && PKGS+=(postgresql postgresql-contrib libpq-dev)
[ "$ENABLE_TLS" = "1" ]  && PKGS+=(certbot python3-certbot-nginx)
apt-get install -y -qq "${PKGS[@]}"

# Require Python >= 3.11 (the app declares requires-python >=3.11).
PYV="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
python3 - <<'PY' || die "Python >= 3.11 required (found $PYV)."
import sys
raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)
PY
log "Python ${PYV} OK."

# ---- 2. Service user -------------------------------------------------------
if ! id -u "$APP_USER" >/dev/null 2>&1; then
  log "Creating service user '${APP_USER}'..."
  useradd --system --create-home --home-dir "/home/${APP_USER}" --shell /usr/sbin/nologin "$APP_USER"
fi

# ---- 3. Fetch application code ---------------------------------------------
log "Fetching application (${REPO_REF}) from ${REPO_URL}..."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$TMP/repo" 2>/dev/null \
  || git clone "$REPO_URL" "$TMP/repo"
[ -d "$TMP/repo/$APP_SUBDIR/app" ] || die "App not found at $APP_SUBDIR in the repo/ref."

mkdir -p "$APP_HOME"
# Sync source (preserve the venv and any local .env across re-runs).
cp -a "$TMP/repo/$APP_SUBDIR/." "$APP_HOME/"
rm -rf "$APP_HOME/.venv/bin/__pycache__" 2>/dev/null || true

# ---- 4. Virtualenv + dependencies -----------------------------------------
log "Building virtualenv and installing dependencies..."
if [ ! -x "$APP_HOME/.venv/bin/python" ]; then
  python3 -m venv "$APP_HOME/.venv"
fi
"$APP_HOME/.venv/bin/pip" install --quiet --upgrade pip wheel
"$APP_HOME/.venv/bin/pip" install --quiet -r "$APP_HOME/requirements.txt"
# Production process manager.
"$APP_HOME/.venv/bin/pip" install --quiet gunicorn
if [ "$ASR_ENGINE" = "mms" ]; then
  warn "Installing MMS speech stack (torch/transformers, ~2GB, may take a while)..."
  "$APP_HOME/.venv/bin/pip" install --quiet torch torchaudio transformers
fi

# ---- 5. Database -----------------------------------------------------------
DB_URL="sqlite:///${APP_HOME}/nko.db"
if [ "$USE_POSTGRES" = "1" ]; then
  log "Provisioning local PostgreSQL database..."
  systemctl enable --now postgresql
  DB_PASS="$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"
  # Create role + db idempotently.
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='nko'" | grep -q 1 \
    || sudo -u postgres psql -qc "CREATE ROLE nko LOGIN PASSWORD '${DB_PASS}';"
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='nko'" | grep -q 1 \
    || sudo -u postgres createdb -O nko nko
  # If the role already existed, reset the password so the .env matches.
  sudo -u postgres psql -qc "ALTER ROLE nko WITH PASSWORD '${DB_PASS}';"
  DB_URL="postgresql+psycopg://nko:${DB_PASS}@127.0.0.1:5432/nko"
fi

# ---- 6. Environment file (secrets) ----------------------------------------
# Preserve an existing secret across re-runs so live JWTs stay valid.
if [ -f "$ENV_FILE" ] && grep -q '^NKO_SECRET_KEY=' "$ENV_FILE"; then
  SECRET="$(grep '^NKO_SECRET_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
  log "Reusing existing NKO_SECRET_KEY."
else
  SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  log "Generated a new NKO_SECRET_KEY."
fi
if [ -f "$ENV_FILE" ] && grep -q '^NKO_REVIEW_API_KEY=' "$ENV_FILE"; then
  REVIEW_KEY="$(grep '^NKO_REVIEW_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
else
  REVIEW_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
  log "Generated a new NKO_REVIEW_API_KEY."
fi

CORS_ORIGINS=""
[ -n "$DOMAIN" ] && CORS_ORIGINS="https://${DOMAIN}"

log "Writing ${ENV_FILE}..."
umask 077
cat > "$ENV_FILE" <<EOF
# Managed by deploy-ubuntu.sh — do not edit by hand while re-running the script.
NKO_SECRET_KEY=${SECRET}
NKO_DATABASE_URL=${DB_URL}
NKO_ASR_ENGINE=${ASR_ENGINE}
NKO_MMS_MODEL_ID=${MMS_MODEL_ID}
NKO_MODEL_VERSION=${MODEL_VERSION}
NKO_REVIEW_API_KEY=${REVIEW_KEY}
NKO_TRAINING_DATA_DIR=${APP_HOME}/training-data
NKO_LLM_PROVIDER=${LLM_PROVIDER}
NKO_LLM_API_KEY=${LLM_API_KEY}
NKO_LLM_MODEL=${LLM_MODEL}
NKO_LLM_BASE_URL=${LLM_BASE_URL}
NKO_ENVIRONMENT=production
NKO_CORS_ORIGINS=${CORS_ORIGINS}
EOF
chown root:"$APP_USER" "$ENV_FILE"
chmod 640 "$ENV_FILE"
umask 022

chown -R "$APP_USER":"$APP_USER" "$APP_HOME"

# ---- 7. systemd service ----------------------------------------------------
if [ -z "$WORKERS" ]; then
  CPUS="$(nproc)"
  WORKERS=$(( CPUS * 2 + 1 ))
  [ "$WORKERS" -gt 8 ] && WORKERS=8
  # SQLite is a single file; keep it to one worker to avoid write contention.
  [ "$USE_POSTGRES" = "1" ] || WORKERS=1
fi
log "Configuring systemd service (${WORKERS} worker(s))..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=N'Ko Voice Transcriptor backend
After=network.target ${USE_POSTGRES:+postgresql.service}
Wants=network-online.target

[Service]
Type=notify
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_HOME}
EnvironmentFile=${ENV_FILE}
ExecStart=${APP_HOME}/.venv/bin/gunicorn app.main:app \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --workers ${WORKERS} \\
    --bind 127.0.0.1:${APP_PORT} \\
    --timeout 120 \\
    --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=3
# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_HOME}
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}" >/dev/null 2>&1 || true
systemctl restart "${SERVICE_NAME}"

# ---- 8. Nginx reverse proxy ------------------------------------------------
log "Configuring Nginx..."
SERVER_NAME="${DOMAIN:-_}"
cat > "/etc/nginx/sites-available/${SERVICE_NAME}" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAME};

    client_max_body_size 12m;   # matches NKO_MAX_UPLOAD_BYTES (10 MiB) + headroom

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF
ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx >/dev/null 2>&1 || true
systemctl reload nginx

# ---- 9. Firewall -----------------------------------------------------------
if [ "$SETUP_FIREWALL" = "1" ]; then
  log "Configuring UFW firewall..."
  ufw allow OpenSSH >/dev/null 2>&1 || true
  ufw allow 'Nginx Full' >/dev/null 2>&1 || true
  ufw --force enable >/dev/null 2>&1 || true
fi

# ---- 10. TLS (optional) ----------------------------------------------------
if [ "$ENABLE_TLS" = "1" ]; then
  log "Requesting Let's Encrypt certificate for ${DOMAIN}..."
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect \
    || warn "certbot failed — check DNS points to this host, then re-run with ENABLE_TLS=1."
fi

# ---- 11. Health check ------------------------------------------------------
log "Waiting for the service to become healthy..."
HEALTHY=0
for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/api/health" >/dev/null 2>&1; then
    HEALTHY=1; break
  fi
  sleep 1
done

echo
if [ "$HEALTHY" = "1" ]; then
  BODY="$(curl -fsS "http://127.0.0.1:${APP_PORT}/api/health")"
  log "Deployment OK. Health: ${BODY}"
else
  warn "Service did not answer /api/health yet. Inspect logs:"
  echo "    journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
fi

echo
log "Summary"
if [ -n "$DOMAIN" ]; then
  SCHEME="http"; [ "$ENABLE_TLS" = "1" ] && SCHEME="https"
  echo "  URL           : ${SCHEME}://${DOMAIN}/"
else
  echo "  URL           : http://<this-server-ip>/"
fi
echo "  App directory : ${APP_HOME}"
echo "  Service       : systemctl status ${SERVICE_NAME}"
echo "  Logs          : journalctl -u ${SERVICE_NAME} -f"
echo "  Env / secrets : ${ENV_FILE}"
echo "  ASR engine    : ${ASR_ENGINE}"
echo "  Model         : ${MMS_MODEL_ID} (${MODEL_VERSION})"
echo "  Review key    : stored in ${ENV_FILE}"
echo "  LLM cleanup   : ${LLM_PROVIDER}"
echo "  Database      : $([ "$USE_POSTGRES" = 1 ] && echo PostgreSQL || echo 'SQLite (single-node)')"
echo
echo "  Update later  : sudo REPO_REF=main $0"
