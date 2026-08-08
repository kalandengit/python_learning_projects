#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Copy .env.example to .env"; exit 1; }
set -a; source .env; set +a
mkdir -p generated
python3 - <<'PY'
import os
from pathlib import Path
src = Path("odoo.conf.template").read_text()
for key in ["ODOO_ADMIN_PASSWD","POSTGRES_USER","POSTGRES_PASSWORD","ODOO_WORKERS"]:
    value = os.environ.get(key)
    if not value or value == "CHANGE_ME":
        raise SystemExit(f"Missing secure value for {key}")
    src = src.replace("${"+key+"}", value)
Path("generated/odoo.conf").write_text(src)
Path("generated/odoo.conf").chmod(0o600)
PY
