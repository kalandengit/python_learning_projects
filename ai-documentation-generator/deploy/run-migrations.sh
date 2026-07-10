#!/usr/bin/env bash
#
# run-migrations.sh — apply the ordered Supabase migrations to your database.
# Uses a throwaway postgres container so nothing needs to be installed on the
# host. Reads SUPABASE_DB_URL from deploy/.env.
#
#   ./run-migrations.sh
#
# Alternative (no psql): open each file in supabase/migrations/ in order and
# paste it into the Supabase dashboard SQL editor, or use `supabase db push`.
set -euo pipefail
cd "$(dirname "$0")"

# shellcheck disable=SC1091
set -a; source .env; set +a
: "${SUPABASE_DB_URL:?Set SUPABASE_DB_URL in deploy/.env}"

MIG_DIR="$(cd .. && pwd)/supabase/migrations"
echo "==> Applying migrations from ${MIG_DIR}"

docker run --rm -v "${MIG_DIR}:/migrations:ro" \
  -e DB_URL="${SUPABASE_DB_URL}" postgres:16-alpine \
  sh -c 'set -e; for f in $(ls /migrations/*.sql | sort); do
           echo "  -> applying $(basename "$f")";
           psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$f";
         done'

echo "==> Migrations applied."
