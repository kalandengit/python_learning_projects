#!/usr/bin/env bash
set -Eeuo pipefail
backup="${1:?Usage: restore.sh backup.dump}"
cd "$(dirname "$0")/.."
set -a; source .env; set +a
sha256sum -c "${backup}.sha256" 2>/dev/null || echo "Checksum sidecar missing or mismatch; verify manually."
docker compose --env-file .env exec -T db \
  pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$backup"
