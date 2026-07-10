#!/usr/bin/env bash
#
# quickstart-root.sh — ONE-SHOT deployment for a fresh Ubuntu/Debian VPS.
# Paste this single line into a root shell (SSH or Linode LISH web console):
#
#   curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/ai-software-studio-framework-b3w9dx/ai-documentation-generator/deploy/quickstart-root.sh | bash
#
# What it does, unattended:
#   1. Installs git, clones the repo to /opt/docdgen (or updates it).
#   2. Runs 00-bootstrap-root.sh  (deploy user + SSH key + Docker + swap + boot enable).
#   3. Creates deploy/.env from the template if missing (placeholder secrets,
#      SITE_ADDRESS=:80, APP URL = this server's IP).
#   4. Builds and starts the full stack (web + worker + redis + caddy).
#   5. Installs the systemd unit -> auto-start on every reboot.
#   6. Runs the smoke test and prints the result.
#
# With placeholder secrets the marketing site serves immediately at http://<ip>.
# Signup/AI/billing activate once you put real Supabase/OpenAI/Stripe keys in
# /opt/docdgen/ai-documentation-generator/deploy/.env and run:
#     cd /opt/docdgen/ai-documentation-generator/deploy && ./run-migrations.sh && ./deploy.sh
set -euo pipefail

REPO_URL="https://github.com/kalandengit/python_learning_projects.git"
BRANCH="claude/ai-software-studio-framework-b3w9dx"
ROOT_DIR="/opt/docdgen"
APP_DIR="${ROOT_DIR}/ai-documentation-generator"
DEPLOY_DIR="${APP_DIR}/deploy"

if [[ $EUID -ne 0 ]]; then echo "Run as root." >&2; exit 1; fi
export DEBIAN_FRONTEND=noninteractive

echo "==> [1/6] Installing git + curl"
apt-get update -qq && apt-get install -y -qq git curl ca-certificates >/dev/null

echo "==> [2/6] Cloning ${REPO_URL} (${BRANCH})"
if [[ -d "${ROOT_DIR}/.git" ]]; then
  git -C "$ROOT_DIR" fetch origin "$BRANCH" && git -C "$ROOT_DIR" checkout "$BRANCH" && git -C "$ROOT_DIR" pull --ff-only origin "$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$ROOT_DIR"
fi

echo "==> [3/6] Bootstrapping (deploy user, SSH key, Docker, swap)"
bash "${DEPLOY_DIR}/00-bootstrap-root.sh"

echo "==> [4/6] Preparing deploy/.env"
SERVER_IP="$(hostname -I | awk '{print $1}')"
if [[ ! -f "${DEPLOY_DIR}/.env" ]]; then
  cp "${DEPLOY_DIR}/.env.production.example" "${DEPLOY_DIR}/.env"
  sed -i "s#^NEXT_PUBLIC_APP_URL=.*#NEXT_PUBLIC_APP_URL=http://${SERVER_IP}#" "${DEPLOY_DIR}/.env"
  echo "    Created .env with PLACEHOLDER secrets (site will serve; auth/AI/billing"
  echo "    stay disabled until you add real Supabase/OpenAI/Stripe keys)."
else
  echo "    Existing .env kept."
fi
chown deploy:deploy "${DEPLOY_DIR}/.env" 2>/dev/null || true
chmod 600 "${DEPLOY_DIR}/.env"
chown -R deploy:deploy "$ROOT_DIR" 2>/dev/null || true

echo "==> [5/6] Building and starting the stack (first build takes several minutes)"
cd "$DEPLOY_DIR"
docker compose up -d --build

echo "==> [5b/6] Enabling auto-start on boot"
sed "s#__DEPLOY_DIR__#${DEPLOY_DIR}#g" docdgen.service > /etc/systemd/system/docdgen.service
systemctl daemon-reload
systemctl enable docker docdgen.service

echo "==> [6/6] Smoke test"
sleep 10
BASE="http://localhost" bash smoke-test.sh || true

cat <<EOF

==========================================================================
 DONE. App: http://${SERVER_IP}
 Auto-start on reboot: enabled (systemd docdgen.service + Docker restart
 policies). Verify anytime with:  systemctl status docdgen

 NEXT STEPS (important):
   1. passwd                      # rotate the root password NOW
   2. Test key login from your machine:
        ssh -i docdgen_deploy_ed25519 deploy@${SERVER_IP}
      then harden SSH:  sudo bash ${DEPLOY_DIR}/10-harden-ssh.sh
   3. Add real secrets:  nano ${DEPLOY_DIR}/.env
      then:  cd ${DEPLOY_DIR} && ./run-migrations.sh && ./deploy.sh
 Logs:  cd ${DEPLOY_DIR} && docker compose logs -f web worker
==========================================================================
EOF
