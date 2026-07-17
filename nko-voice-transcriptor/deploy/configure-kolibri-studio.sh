#!/usr/bin/env bash
# Configure kolibri-studio.service on localhost:9090 behind Nginx + HTTPS.
set -Eeuo pipefail

DOMAIN="${DOMAIN:-kolibri.studio.kalanfa.org}"
EMAIL="${EMAIL:-contact@kalanfa.org}"
SERVICE="${SERVICE:-kolibri-studio.service}"
PORT="${PORT:-9090}"
NGINX_SITE="/etc/nginx/sites-available/kolibri-studio"
OVERRIDE_DIR="/etc/systemd/system/${SERVICE}.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/port.conf"

die() { echo "ERROR: $*" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || die "Run this script with sudo."
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid domain."
[[ "$SERVICE" =~ ^[A-Za-z0-9_.@-]+\.service$ ]] || die "Invalid service name."
[[ "$PORT" =~ ^[0-9]+$ ]] && [ "$PORT" -ge 1024 ] && [ "$PORT" -le 65535 ] || die "Invalid port."
systemctl cat "$SERVICE" >/dev/null 2>&1 || die "Service not found: $SERVICE"

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

BACKUP=""
if [ -f "$OVERRIDE_FILE" ]; then
  BACKUP="${OVERRIDE_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
  cp -a "$OVERRIDE_FILE" "$BACKUP"
fi
mkdir -p "$OVERRIDE_DIR"
cat > "$OVERRIDE_FILE" <<EOF
[Service]
# Common port variables; the service uses whichever its launcher supports.
Environment=PORT=$PORT
Environment=KOLIBRI_PORT=$PORT
Environment=KOLIBRI_HTTP_PORT=$PORT
Environment=DJANGO_PORT=$PORT
EOF

rollback() {
  echo "Rolling back the port override..."
  if [ -n "$BACKUP" ]; then cp -a "$BACKUP" "$OVERRIDE_FILE"; else rm -f "$OVERRIDE_FILE"; fi
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
  die "The application does not recognize the standard port variables. Send: systemctl cat $SERVICE"
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
