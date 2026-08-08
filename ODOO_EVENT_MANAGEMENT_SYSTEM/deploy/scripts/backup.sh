#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ems-odoo}"
mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose --env-file .env exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  > "$BACKUP_DIR/db-${stamp}.dump"
sha256sum "$BACKUP_DIR/db-${stamp}.dump" > "$BACKUP_DIR/db-${stamp}.dump.sha256"
find "$BACKUP_DIR" -type f -mtime +14 -delete
echo "$BACKUP_DIR/db-${stamp}.dump"
