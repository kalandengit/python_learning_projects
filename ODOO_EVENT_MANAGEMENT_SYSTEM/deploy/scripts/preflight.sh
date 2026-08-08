#!/usr/bin/env bash
set -Eeuo pipefail
echo "== EMS Odoo VPS preflight =="
. /etc/os-release && echo "$PRETTY_NAME"
df -h /
free -h
ss -lntup || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}' || true
nginx -t || true
ls -la /etc/nginx/sites-enabled 2>/dev/null || true
