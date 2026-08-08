#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
./scripts/render-config.sh
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose --env-file .env ps
