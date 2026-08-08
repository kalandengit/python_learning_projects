#!/usr/bin/env bash
# Publish the EMS site through the host's Nginx, coexisting with other vhosts.
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${ODOO_DOMAIN:?}"
: "${ODOO_PORT:?}"
: "${LETSENCRYPT_EMAIL:?}"

server_ip="$(curl -4 -fsS https://api.ipify.org || true)"
dns_ip="$(getent ahostsv4 "$ODOO_DOMAIN" | awk 'NR==1 {print $1}')"
echo "Server IPv4: ${server_ip:-unknown}"
echo "DNS IPv4:    ${dns_ip:-unresolved}"

if [[ -z "$dns_ip" ]]; then
  echo "$ODOO_DOMAIN does not resolve. Point DNS at this VPS first." >&2
  exit 2
fi
if [[ -n "$server_ip" && "$server_ip" != "$dns_ip" ]]; then
  echo "$ODOO_DOMAIN resolves to $dns_ip, not to this host ($server_ip)." >&2
  echo "Certbot would fail the HTTP-01 challenge. Fix DNS first." >&2
  exit 2
fi

mkdir -p /var/www/certbot

# Step 1: plain HTTP vhost so certbot can answer the ACME challenge.
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
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  }
}
EOF
ln -sfn /etc/nginx/sites-available/ems-odoo.conf /etc/nginx/sites-enabled/ems-odoo.conf
nginx -t && systemctl reload nginx

# Step 2: obtain the certificate.
certbot certonly --webroot -w /var/www/certbot --non-interactive --agree-tos \
  --email "$LETSENCRYPT_EMAIL" -d "$ODOO_DOMAIN"

# Step 3: swap in the full TLS vhost.
export ODOO_DOMAIN ODOO_PORT
envsubst '${ODOO_DOMAIN} ${ODOO_PORT}' < nginx/ems-odoo.conf.template \
  > /etc/nginx/sites-available/ems-odoo.conf
nginx -t && systemctl reload nginx

echo "EMS is published at https://${ODOO_DOMAIN}"
echo "Other vhosts on this host are untouched; Odoo stays bound to 127.0.0.1:${ODOO_PORT}."
