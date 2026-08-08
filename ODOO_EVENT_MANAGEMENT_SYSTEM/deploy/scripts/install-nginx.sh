#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${ODOO_DOMAIN:?}"
: "${ODOO_PORT:?}"
: "${LETSENCRYPT_EMAIL:?}"

server_ip="$(curl -4 -fsS https://api.ipify.org || true)"
dns_ip="$(getent ahostsv4 "$ODOO_DOMAIN" | awk 'NR==1 {print $1}')"
echo "Server IPv4: $server_ip"
echo "DNS IPv4: $dns_ip"
[[ -z "$server_ip" || -z "$dns_ip" || "$server_ip" == "$dns_ip" ]] || {
  echo "DNS does not point to this VPS"; exit 2;
}

cat >/etc/nginx/sites-available/ems-odoo.conf <<EOF
server {
  listen 80;
  listen [::]:80;
  server_name ${ODOO_DOMAIN};
  location /.well-known/acme-challenge/ { root /var/www/certbot; }
  location / {
    proxy_pass http://127.0.0.1:${ODOO_PORT};
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-Proto http;
  }
}
EOF
ln -sfn /etc/nginx/sites-available/ems-odoo.conf /etc/nginx/sites-enabled/ems-odoo.conf
nginx -t && systemctl reload nginx

certbot --nginx --non-interactive --agree-tos --redirect \
  --email "$LETSENCRYPT_EMAIL" -d "$ODOO_DOMAIN"

export ODOO_DOMAIN ODOO_PORT
envsubst '${ODOO_DOMAIN} ${ODOO_PORT}' < nginx/ems-odoo.conf.template \
  > /etc/nginx/sites-available/ems-odoo.conf
nginx -t && systemctl reload nginx
