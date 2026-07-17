#!/usr/bin/env bash
# Install a tiny authenticated dashboard on its own HTTPS hostname.
set -Eeuo pipefail

DOMAIN="${DOMAIN:-admin.saas.kalanfa.org}"
EMAIL="${EMAIL:-contact@kalanfa.org}"
NKO_UNIT="${NKO_UNIT:-nko-transcriptor.service}"
KOLIBRI_UNIT="${KOLIBRI_UNIT:-}"
# Optional semicolon-separated entries: key|Display name|unit.service
# Example: EXTRA_SERVICES='nextcloud|Nextcloud|nextcloud.service;worker|Queue worker|worker.service'
EXTRA_SERVICES="${EXTRA_SERVICES:-}"
ADMIN_LOGIN="${ADMIN_LOGIN:-admin}"
ADMIN_PORT="${ADMIN_PORT:-8765}"
SOURCE_URL="${SOURCE_URL:-https://raw.githubusercontent.com/kalandengit/python_learning_projects/agent/nko-voice-1.8.0/nko-voice-transcriptor/deploy/admin-dashboard.py}"
NGINX_SITE="${NGINX_SITE:-/etc/nginx/sites-available/nko-admin-dashboard}"
APP_DIR=/opt/nko-admin-dashboard
APP_USER=nko-admin

die() { echo "ERROR: $*" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || die "Run with sudo."
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid DOMAIN."
[[ "$NKO_UNIT" =~ ^[A-Za-z0-9_.@-]+\.service$ ]] || die "Invalid NKO_UNIT."

if [ -z "$KOLIBRI_UNIT" ]; then
  for candidate in kolibri-studio.service kolibri.service; do
    if systemctl cat "$candidate" >/dev/null 2>&1; then KOLIBRI_UNIT="$candidate"; break; fi
  done
fi
if [ -z "$KOLIBRI_UNIT" ]; then
  echo "Detected Kolibri-related system services:"
  systemctl list-unit-files --type=service --no-legend | grep -i kolibri || true
  die "Kolibri systemd service not detected. Re-run with KOLIBRI_UNIT=its-name.service"
fi
[[ "$KOLIBRI_UNIT" =~ ^[A-Za-z0-9_.@-]+\.service$ ]] || die "Invalid KOLIBRI_UNIT."
systemctl cat "$NKO_UNIT" >/dev/null 2>&1 || die "Service not found: $NKO_UNIT"
systemctl cat "$KOLIBRI_UNIT" >/dev/null 2>&1 || die "Service not found: $KOLIBRI_UNIT"
RESOLVED_IP="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}')"
PUBLIC_IP="$(curl -4fsS https://api.ipify.org || true)"
[ -n "$RESOLVED_IP" ] || die "DNS is not active for $DOMAIN. Create its A record first."
if [ -n "$PUBLIC_IP" ] && [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
  die "$DOMAIN points to $RESOLVED_IP, but this VPS is $PUBLIC_IP."
fi

if [ -z "${ADMIN_PASSWORD:-}" ]; then
  read -r -s -p "Choose a password for ${ADMIN_LOGIN}: " ADMIN_PASSWORD </dev/tty
  echo >/dev/tty
  read -r -s -p "Confirm password: " ADMIN_PASSWORD_CONFIRM </dev/tty
  echo >/dev/tty
  [ "$ADMIN_PASSWORD" = "$ADMIN_PASSWORD_CONFIRM" ] || die "Passwords do not match."
fi
[ "${#ADMIN_PASSWORD}" -ge 12 ] || die "Use a password of at least 12 characters."

echo "Installing lightweight dashboard for $NKO_UNIT and $KOLIBRI_UNIT..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 nginx apache2-utils curl sudo certbot python3-certbot-nginx
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
install -d -o root -g "$APP_USER" -m 0750 "$APP_DIR"
curl -fsSL "$SOURCE_URL" -o "$APP_DIR/admin-dashboard.py"
chown root:"$APP_USER" "$APP_DIR/admin-dashboard.py"
chmod 0750 "$APP_DIR/admin-dashboard.py"

SERVICE_ENTRIES="nko|N'Ko Voice Transcriptor|$NKO_UNIT;kolibri|Kolibri Studio|$KOLIBRI_UNIT"
SERVICE_UNITS=("$NKO_UNIT" "$KOLIBRI_UNIT")
if [ -n "$EXTRA_SERVICES" ]; then
  IFS=';' read -ra EXTRAS <<< "$EXTRA_SERVICES"
  for entry in "${EXTRAS[@]}"; do
    IFS='|' read -r key label unit extra <<< "$entry"
    [[ "$key" =~ ^[a-z][a-z0-9_-]*$ ]] || die "Invalid extra service key: $key"
    [ -n "$label" ] && [ -z "${extra:-}" ] || die "Use key|Display name|unit.service for EXTRA_SERVICES."
    [[ "$label" != *"'"* ]] || die "An extra service label cannot contain a single quote."
    [[ "$unit" =~ ^[A-Za-z0-9_.@-]+\.service$ ]] || die "Invalid extra service unit: $unit"
    systemctl cat "$unit" >/dev/null 2>&1 || die "Service not found: $unit"
    SERVICE_ENTRIES+=";$key|$label|$unit"
    SERVICE_UNITS+=("$unit")
  done
fi

CSRF_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
umask 077
cat > /etc/nko-admin-dashboard.env <<EOF
ADMIN_BIND=127.0.0.1
ADMIN_PORT=$ADMIN_PORT
ADMIN_CSRF_TOKEN=$CSRF_TOKEN
ADMIN_SERVICES='$SERVICE_ENTRIES'
EOF
chown root:"$APP_USER" /etc/nko-admin-dashboard.env
chmod 0640 /etc/nko-admin-dashboard.env

SYSTEMCTL="$(command -v systemctl)"
SUDOERS=/etc/sudoers.d/nko-admin-dashboard
: > "$SUDOERS"
for unit in "${SERVICE_UNITS[@]}"; do
  echo "$APP_USER ALL=(root) NOPASSWD: $SYSTEMCTL start $unit, $SYSTEMCTL stop $unit, $SYSTEMCTL restart $unit" >> "$SUDOERS"
done
chmod 0440 "$SUDOERS"
visudo -cf "$SUDOERS" >/dev/null

cat > /etc/systemd/system/nko-admin-dashboard.service <<EOF
[Unit]
Description=Lightweight N'Ko and Kolibri administration dashboard
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
EnvironmentFile=/etc/nko-admin-dashboard.env
ExecStart=/usr/bin/python3 $APP_DIR/admin-dashboard.py
Restart=on-failure
RestartSec=3
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryMax=64M
TasksMax=16

[Install]
WantedBy=multi-user.target
EOF

printf '%s\n' "$ADMIN_PASSWORD" | htpasswd -i -c /etc/nginx/nko-admin.htpasswd "$ADMIN_LOGIN" >/dev/null
chmod 0640 /etc/nginx/nko-admin.htpasswd
chown root:www-data /etc/nginx/nko-admin.htpasswd
cat > "$NGINX_SITE" <<EOF
server {
  listen 80;
  listen [::]:80;
  server_name $DOMAIN;

  location / {
    auth_basic "VPS administration";
    auth_basic_user_file /etc/nginx/nko-admin.htpasswd;
    proxy_pass http://127.0.0.1:$ADMIN_PORT/;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 35s;
  }
}
EOF
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/nko-admin-dashboard

systemctl daemon-reload
systemctl enable --now nko-admin-dashboard.service
nginx -t
systemctl reload nginx
certbot --nginx --domain "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive --redirect
nginx -t
systemctl reload nginx
curl -fsS "http://127.0.0.1:$ADMIN_PORT/health" >/dev/null
echo
echo "SUCCESS: https://$DOMAIN/"
echo "Login: $ADMIN_LOGIN"
echo "Controlled services: ${SERVICE_UNITS[*]}"
echo "Add more later by re-running with EXTRA_SERVICES='key|Display name|unit.service'"
echo "The password is not printed or stored in plain text."
