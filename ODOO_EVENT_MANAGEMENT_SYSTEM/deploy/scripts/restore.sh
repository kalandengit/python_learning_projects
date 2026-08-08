#!/usr/bin/env bash
# Restore a backup produced by backup.sh.
#
# Usage: restore.sh /var/backups/ems-odoo/db-<stamp>.dump [filestore-<stamp>.tar.gz]
#
# Odoo is stopped for the duration: pg_restore --clean cannot drop objects that
# a running server holds open, and a half-restored database served to users is
# worse than a short, announced outage.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

dump="${1:?Usage: restore.sh DB_DUMP [FILESTORE_TARBALL]}"
filestore="${2:-}"
DB="${ODOO_DB:?ODOO_DB must be set in .env}"

[[ -f "$dump" ]] || { echo "No such dump: $dump" >&2; exit 1; }

stamp="$(basename "$dump")"; stamp="${stamp#db-}"; stamp="${stamp%.dump}"
sidecar="$(dirname "$dump")/backup-${stamp}.sha256"
if [[ -f "$sidecar" ]]; then
  ( cd "$(dirname "$dump")" && sha256sum -c "$(basename "$sidecar")" )
else
  echo "Checksum sidecar $sidecar is missing." >&2
  echo "Refusing to restore an unverified backup. Pass a verified copy." >&2
  exit 2
fi

echo "Stopping Odoo..."
docker compose --env-file .env stop odoo

echo "Restoring database $DB..."
docker compose --env-file .env exec -T db \
  pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$DB" < "$dump"

if [[ -n "$filestore" ]]; then
  [[ -f "$filestore" ]] || { echo "No such filestore: $filestore" >&2; exit 1; }
  echo "Restoring filestore..."
  docker compose --env-file .env run --rm -T --entrypoint sh odoo -c \
    'rm -rf /var/lib/odoo/* && tar xzf - -C /var/lib/odoo' < "$filestore"
fi

echo "Starting Odoo..."
docker compose --env-file .env start odoo
docker compose --env-file .env ps
echo "Restore complete. Verify by logging in and opening EMS > Tickets."
