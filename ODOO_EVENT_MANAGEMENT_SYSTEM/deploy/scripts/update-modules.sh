#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
db="${1:?Usage: update-modules.sh DATABASE_NAME}"
docker compose --env-file .env exec -T odoo \
  odoo -d "$db" -u ems_suite --stop-after-init --log-level=info
