#!/usr/bin/env bash
#
# deploy.sh — run as the 'deploy' user from this directory to build, launch,
# and register the stack for auto-start on boot.
#
#   cd /opt/docdgen/ai-documentation-generator/deploy
#   cp .env.production.example .env && nano .env   # fill in real secrets first
#   ./deploy.sh
#
# Re-runnable: pulls the latest build, restarts changed services, and refreshes
# the systemd unit. Safe to run after every `git pull`.
set -euo pipefail
cd "$(dirname "$0")"
DEPLOY_DIR="$(pwd)"

if [[ ! -f .env ]]; then
  echo "!! deploy/.env not found. Copy the template and fill it in:"
  echo "   cp .env.production.example .env && nano .env"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "!! Docker Compose not available. Run 00-bootstrap-root.sh as root first," \
       "and make sure you re-logged in so the 'docker' group applies." >&2
  exit 1
fi

echo "==> Building and starting the stack (web, worker, redis, caddy)"
docker compose up -d --build

echo "==> Installing systemd unit for auto-start on boot"
UNIT=/etc/systemd/system/docdgen.service
sed "s#__DEPLOY_DIR__#${DEPLOY_DIR}#g" docdgen.service | sudo tee "$UNIT" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable docdgen.service
sudo systemctl enable docker

echo "==> Waiting for the app to become healthy..."
sleep 8
docker compose ps

echo
echo "==> Running smoke test"
bash smoke-test.sh || {
  echo "Smoke test did not pass yet. Check logs with:"
  echo "   docker compose logs -f web worker"
  exit 1
}

echo
echo "Deploy complete. The stack will auto-start on every reboot."
echo "Manage it with: docker compose ps | logs -f | restart | down"
