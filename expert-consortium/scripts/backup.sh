#!/usr/bin/env bash
# Back up everything personal: knowledge base, uploads, chat logs, fine-tune data.
# Usage: ./scripts/backup.sh [destination-dir]   (default: ./backups)
set -euo pipefail

cd "$(dirname "$0")/.."
DEST="${1:-backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"

# Embedded Qdrant lives in data/; Docker Qdrant lives in a named volume.
if docker compose ps qdrant --status running >/dev/null 2>&1 && [ -n "$(docker compose ps -q qdrant 2>/dev/null)" ]; then
  echo "Snapshotting Docker Qdrant volume..."
  docker run --rm \
    -v "$(docker compose ps -q qdrant | xargs docker inspect -f '{{ range .Mounts }}{{ if eq .Destination "/qdrant/storage" }}{{ .Name }}{{ end }}{{ end }}')":/storage:ro \
    -v "$(pwd)/$DEST":/backup alpine \
    tar czf "/backup/qdrant-$STAMP.tar.gz" -C /storage .
fi

tar czf "$DEST/consortium-$STAMP.tar.gz" \
  --exclude='.venv' --exclude='__pycache__' \
  uploads logs finetune_data data 2>/dev/null || true

echo "✓ Backup written to $DEST/"
ls -lh "$DEST" | tail -3
