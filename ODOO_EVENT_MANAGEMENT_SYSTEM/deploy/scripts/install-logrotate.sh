#!/usr/bin/env bash
# Install the host logrotate policy for the container's Odoo log file.
#
# copytruncate is used deliberately: the Odoo process inside the container holds
# the file open, and rotating by rename would leave it writing to the rotated
# inode until the next restart.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }

volume="$(docker volume inspect --format '{{ .Mountpoint }}' \
  "$(basename "$PWD")_ems_odoo_log" 2>/dev/null || true)"

if [[ -z "$volume" ]]; then
  echo "Could not resolve the ems_odoo_log volume mountpoint." >&2
  echo "Start the stack first (scripts/deploy.sh), then re-run this script." >&2
  exit 2
fi

sed "s#__ODOO_LOG_PATH__#${volume}#" logrotate/ems-odoo > /etc/logrotate.d/ems-odoo
chmod 0644 /etc/logrotate.d/ems-odoo

logrotate --debug /etc/logrotate.d/ems-odoo
echo "Installed /etc/logrotate.d/ems-odoo for ${volume}"
