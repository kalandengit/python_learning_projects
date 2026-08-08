#!/usr/bin/env bash
# Upgrade the EMS suite in place, taking a rollback point first.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

db="${1:-${ODOO_DB:?Pass a database name or set ODOO_DB in .env}}"

echo "== Taking a pre-upgrade backup (rollback point) =="
./scripts/backup.sh

echo "== Upgrading ems_suite on $db =="
docker compose --env-file .env exec -T odoo \
  odoo -d "$db" -u ems_suite --stop-after-init --log-level=info

echo "== Restarting =="
docker compose --env-file .env restart odoo
docker compose --env-file .env ps

cat <<'EOF'

If the upgrade misbehaved, roll back with the backup printed above:

  ./scripts/restore.sh /var/backups/ems-odoo/db-<stamp>.dump \
                       /var/backups/ems-odoo/filestore-<stamp>.tar.gz

EOF
