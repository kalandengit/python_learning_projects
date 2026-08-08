#!/usr/bin/env bash
# Back up the EMS database and filestore, with a checksum sidecar.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

BACKUP_DIR="${BACKUP_DIR:-/var/backups/ems-odoo}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
DB="${ODOO_DB:?ODOO_DB must be set in .env}"

mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump="$BACKUP_DIR/db-${stamp}.dump"
filestore="$BACKUP_DIR/filestore-${stamp}.tar.gz"

# -Fc custom format so restore.sh can use pg_restore --clean --if-exists.
docker compose --env-file .env exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$DB" -Fc > "$dump"

# The filestore holds attachments; a database-only backup restores to a site
# with broken documents, so both are captured under the same timestamp.
docker compose --env-file .env exec -T odoo \
  tar czf - -C /var/lib/odoo . > "$filestore"

( cd "$BACKUP_DIR" && sha256sum "$(basename "$dump")" "$(basename "$filestore")" \
    > "backup-${stamp}.sha256" )

chmod 0600 "$dump" "$filestore" "$BACKUP_DIR/backup-${stamp}.sha256"

find "$BACKUP_DIR" -type f -mtime "+${RETENTION_DAYS}" -delete

echo "$dump"
echo "$filestore"
