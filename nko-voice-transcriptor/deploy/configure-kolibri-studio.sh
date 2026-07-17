#!/usr/bin/env bash
# Configure kolibri-studio.service on localhost:9090 behind Nginx + HTTPS.
set -Eeuo pipefail

DOMAIN="${DOMAIN:-kolibri.studio.kalanfa.org}"
EMAIL="${EMAIL:-contact@kalanfa.org}"
SERVICE="${SERVICE:-kolibri-studio.service}"
PORT="${PORT:-9090}"
NGINX_SITE="/etc/nginx/sites-available/kolibri-studio"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/kolibri-studio/deploy}"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.deploy.yml"
COMPOSE_ENV="$COMPOSE_DIR/.env"

die() { echo "ERROR: $*" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || die "Run this script with sudo."
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid domain."
[[ "$SERVICE" =~ ^[A-Za-z0-9_.@-]+\.service$ ]] || die "Invalid service name."
[[ "$PORT" =~ ^[0-9]+$ ]] && [ "$PORT" -ge 1024 ] && [ "$PORT" -le 65535 ] || die "Invalid port."
systemctl cat "$SERVICE" >/dev/null 2>&1 || die "Service not found: $SERVICE"
[ -f "$COMPOSE_FILE" ] || die "Compose file not found: $COMPOSE_FILE"
[ -f "$COMPOSE_ENV" ] || die "Compose environment not found: $COMPOSE_ENV"

echo "Checking DNS..."
RESOLVED_IP="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}')"
PUBLIC_IP="$(curl -4fsS https://api.ipify.org || true)"
echo "Domain IP: ${RESOLVED_IP:-not found}"
echo "VPS IP:    ${PUBLIC_IP:-unknown}"
[ -n "$RESOLVED_IP" ] || die "Create A record: $DOMAIN -> $PUBLIC_IP"
if [ -n "$PUBLIC_IP" ] && [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
  die "DNS points to $RESOLVED_IP instead of $PUBLIC_IP."
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx curl ca-certificates

STAMP="$(date +%Y%m%d-%H%M%S)"
ENV_BACKUP="${COMPOSE_ENV}.backup-${STAMP}"
COMPOSE_BACKUP="${COMPOSE_FILE}.backup-${STAMP}"
cp -a "$COMPOSE_ENV" "$ENV_BACKUP"
cp -a "$COMPOSE_FILE" "$COMPOSE_BACKUP"

# Remove the obsolete override created by older versions of this installer.
rm -f "/etc/systemd/system/${SERVICE}.d/port.conf"

python3 - "$COMPOSE_ENV" "$COMPOSE_FILE" "$PORT" <<'PY'
import pathlib
import re
import sys

env_path = pathlib.Path(sys.argv[1])
compose_path = pathlib.Path(sys.argv[2])
port = sys.argv[3]
env = env_path.read_text()
if re.search(r"(?m)^STUDIO_HTTP_PORT=.*$", env):
    env = re.sub(r"(?m)^STUDIO_HTTP_PORT=.*$", f"STUDIO_HTTP_PORT={port}", env)
else:
    env += f"\nSTUDIO_HTTP_PORT={port}\n"
env_path.write_text(env)

compose = compose_path.read_text()
old = '      - "${STUDIO_HTTP_PORT:-8080}:8080"'
already = '      - "127.0.0.1:${STUDIO_HTTP_PORT:-9090}:8080"'
if old in compose:
    compose = compose.replace(old, already, 1)
elif already not in compose:
    raise SystemExit("Expected STUDIO_HTTP_PORT mapping not found in Compose file")
compose_path.write_text(compose)
PY

rollback() {
  echo "Rolling back the Compose port configuration..."
  cp -a "$ENV_BACKUP" "$COMPOSE_ENV"
  cp -a "$COMPOSE_BACKUP" "$COMPOSE_FILE"
  systemctl daemon-reload
  systemctl restart "$SERVICE" || true
}

systemctl daemon-reload
if ! systemctl restart "$SERVICE"; then
  rollback
  die "$SERVICE failed to restart. Inspect: journalctl -u $SERVICE -n 80 --no-pager"
fi

echo "Waiting for Kolibri Studio on 127.0.0.1:$PORT..."
READY=0
for _ in $(seq 1 30); do
  if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
if [ "$READY" != 1 ]; then
  echo "The service did not accept HTTP connections on port $PORT."
  systemctl status "$SERVICE" --no-pager || true
  ss -ltnp | grep -E ':(8000|8080|9090)\b' || true
  rollback
  die "Kolibri did not start on port $PORT; its previous Compose configuration was restored."
fi

cat > "$NGINX_SITE" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    client_max_body_size 1g;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/kolibri-studio
nginx -t
systemctl reload nginx

certbot --nginx --domain "$DOMAIN" --email "$EMAIL" \
  --agree-tos --non-interactive --redirect
nginx -t
systemctl reload nginx

echo
echo "SUCCESS"
echo "Kolibri local address: http://127.0.0.1:$PORT"
echo "Kolibri public URL:    https://$DOMAIN/"
echo "Service status:        systemctl status $SERVICE"
echo "Logs:                  journalctl -u $SERVICE -f"
