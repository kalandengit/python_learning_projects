#!/usr/bin/env bash
# Offline validation of the deployment stack. Runs without a VPS, without DNS
# and without starting any container, so it is safe in CI.
#
#   ./scripts/validate-stack.sh
set -Eeuo pipefail
cd "$(dirname "$0")/.."

fail=0
step() { printf '\n== %s ==\n' "$1"; }
ok()   { printf '  OK   %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; fail=1; }

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

step "Rendering odoo.conf from a throwaway .env"
if [[ -f .env ]]; then
  cp .env "$workdir/.env.backup"
fi
sed -e 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=validate-only-not-a-secret/' \
    -e 's/^ODOO_ADMIN_PASSWD=.*/ODOO_ADMIN_PASSWD=validate-only-not-a-secret/' \
    .env.example > .env.validate
cp .env.validate .env
if ./scripts/render-config.sh >/dev/null; then
  ok "render-config.sh produced generated/odoo.conf"
  grep -q 'dbfilter = \^ems_production\$' generated/odoo.conf \
    && ok "dbfilter is pinned to the configured database" \
    || bad "dbfilter was not pinned"
  grep -q 'list_db = False' generated/odoo.conf \
    && ok "database manager listing is disabled" \
    || bad "list_db is not False"
  [[ "$(stat -c '%a' generated/odoo.conf)" == "600" ]] \
    && ok "rendered config is 0600" \
    || bad "rendered config permissions are not 0600"
else
  bad "render-config.sh failed"
fi

step "render-config.sh refuses placeholder secrets"
sed -e 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=CHANGE_ME/' .env.example > .env
if ./scripts/render-config.sh >/dev/null 2>&1; then
  bad "rendered a config while POSTGRES_PASSWORD was still CHANGE_ME"
else
  ok "refused to render with a CHANGE_ME secret"
fi
cp .env.validate .env

step "Nginx configuration"
if command -v nginx >/dev/null; then
  export ODOO_DOMAIN=validate.example.com ODOO_PORT=19069
  mkdir -p "$workdir/conf.d" "$workdir/certs"
  envsubst '${ODOO_DOMAIN} ${ODOO_PORT}' < nginx/ems-odoo.conf.template \
    > "$workdir/conf.d/ems-odoo.conf"
  # nginx -t loads the certificate, so give it a self-signed throwaway pair.
  openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
    -subj "/CN=${ODOO_DOMAIN}" \
    -keyout "$workdir/certs/privkey.pem" -out "$workdir/certs/fullchain.pem" \
    >/dev/null 2>&1
  sed -i "s#/etc/letsencrypt/live/${ODOO_DOMAIN}#${workdir}/certs#g" \
    "$workdir/conf.d/ems-odoo.conf"
  # `nginx -t` really opens the listen sockets, so on a host without IPv6 the
  # `listen [::]` lines fail for reasons that have nothing to do with this
  # configuration. Drop them for the syntax check and say so.
  if [[ ! -f /proc/net/if_inet6 ]]; then
    echo "  NOTE host has no IPv6; testing without the listen [::] directives"
    sed -i '/listen \[::\]/d' "$workdir/conf.d/ems-odoo.conf"
  fi
  cat > "$workdir/nginx.conf" <<EOF
events {}
http {
  include ${workdir}/conf.d/*.conf;
}
EOF
  if nginx -t -c "$workdir/nginx.conf" -p "$workdir" 2>&1 | tail -2; then
    ok "nginx -t passed"
    grep -q '/websocket' "$workdir/conf.d/ems-odoo.conf" && ok "/websocket is proxied" \
      || bad "/websocket block is missing"
    grep -q 'Strict-Transport-Security' "$workdir/conf.d/ems-odoo.conf" \
      && ok "HSTS header present" || bad "HSTS header missing"
  else
    bad "nginx -t failed"
  fi
else
  echo "  SKIP nginx is not installed on this host"
fi

step "Compose file"
if command -v docker >/dev/null; then
  if docker compose --env-file .env config >"$workdir/compose.resolved" 2>"$workdir/compose.err"; then
    ok "docker compose config parsed"
    # `docker compose config` normalises ports to long form.
    if grep -q 'host_ip: 127.0.0.1' "$workdir/compose.resolved" \
       && ! grep -qE 'host_ip: (0\.0\.0\.0|::)' "$workdir/compose.resolved"; then
      ok "Odoo port is bound to loopback only"
    else
      bad "Odoo port is not loopback-bound"
    fi
    grep -qE '^\s+db:' "$workdir/compose.resolved" && ok "db service defined" || bad "db service missing"
    if grep -A20 -E '^\s+db:' "$workdir/compose.resolved" | grep -q 'published:'; then
      bad "the database publishes a host port"
    else
      ok "database publishes no host port"
    fi
  else
    bad "docker compose config failed: $(tail -1 "$workdir/compose.err")"
  fi
else
  echo "  SKIP docker is not installed on this host"
fi

step "No committed secrets"
# Patterns are assembled at runtime so this script does not match itself.
live_key="sk_""live_"
private_key="BEGIN ""PRIVATE KEY"
if grep -rIl --exclude-dir=generated --exclude='.env' --exclude='.env.validate' \
     --exclude="$(basename "$0")" \
     -e "$live_key" -e "$private_key" . >/dev/null 2>&1; then
  bad "a possible production secret is present in deploy/"
else
  ok "no live keys or private keys in deploy/"
fi

rm -f .env .env.validate generated/odoo.conf
if [[ -f "$workdir/.env.backup" ]]; then
  cp "$workdir/.env.backup" .env
fi

printf '\n'
if [[ $fail -eq 0 ]]; then
  echo "STACK VALIDATION: PASS"
else
  echo "STACK VALIDATION: FAIL"
fi
exit $fail
