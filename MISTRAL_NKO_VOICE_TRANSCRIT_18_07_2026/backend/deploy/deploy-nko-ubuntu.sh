#!/usr/bin/env bash
# Ubuntu 24.04/26.04 production deploy: system deps, venv, systemd, nginx, TLS.
# Run as root from the backend/ directory. Review before running.
set -euo pipefail

APP_DIR=/opt/nko-voice
APP_USER=nko
DOMAIN="${DOMAIN:-nko.example.com}"

echo "==> Installing system packages"
apt-get update
apt-get install -y python3.11 python3.11-venv postgresql nginx certbot python3-certbot-nginx ufw

echo "==> Creating service user and directories"
id -u "$APP_USER" &>/dev/null || useradd --system --create-home "$APP_USER"
mkdir -p "$APP_DIR"
cp -r . "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "==> Python environment"
sudo -u "$APP_USER" python3.11 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements-lock.txt"

echo "==> PostgreSQL (least-privilege role)"
sudo -u postgres psql <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nko') THEN
    CREATE ROLE nko LOGIN PASSWORD 'CHANGE-ME';
  END IF;
END $$;
SELECT 'CREATE DATABASE nko OWNER nko' WHERE NOT EXISTS
  (SELECT FROM pg_database WHERE datname = 'nko') \gexec
SQL

echo "==> Environment file (edit $APP_DIR/.env before first start!)"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  sed -i "s|^NKO_SECRET_KEY=.*|NKO_SECRET_KEY=$(openssl rand -hex 32)|" "$APP_DIR/.env"
  sed -i "s|^NKO_DATABASE_URL=.*|NKO_DATABASE_URL=postgresql+psycopg://nko:CHANGE-ME@localhost:5432/nko|" "$APP_DIR/.env"
  chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

echo "==> Database migrations"
cd "$APP_DIR" && sudo -u "$APP_USER" "$APP_DIR/.venv/bin/alembic" upgrade head

echo "==> systemd service"
cat > /etc/systemd/system/nko-voice.service <<EOF
[Unit]
Description=N'Ko Voice Transcriptor
After=network.target postgresql.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now nko-voice

echo "==> nginx + TLS"
sed "s/nko.example.com/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/nko-voice
ln -sf /etc/nginx/sites-available/nko-voice /etc/nginx/sites-enabled/nko-voice
nginx -t && systemctl reload nginx
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN" || \
  echo "!! certbot failed — run manually: certbot --nginx -d $DOMAIN"

echo "==> Firewall"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Done. Edit $APP_DIR/.env (DB password!), then: systemctl restart nko-voice"
