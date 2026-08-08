#!/usr/bin/env bash
# Render deploy/generated/odoo.conf from .env. Refuses to render placeholders.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

test -f .env || { echo "Copy .env.example to .env first."; exit 1; }
set -a; source .env; set +a

mkdir -p generated
python3 - <<'PY'
import os
import re
from pathlib import Path

REQUIRED = [
    "ODOO_ADMIN_PASSWD", "POSTGRES_USER", "POSTGRES_PASSWORD",
    "ODOO_WORKERS", "ODOO_DB",
]

src = Path("odoo.conf.template").read_text()
for key in REQUIRED:
    value = os.environ.get(key, "")
    if not value or value == "CHANGE_ME":
        raise SystemExit(f"Refusing to render: {key} is unset or still CHANGE_ME")
    src = src.replace("${" + key + "}", value)

leftover = re.findall(r"\$\{([A-Z_]+)\}", src)
if leftover:
    raise SystemExit(f"Refusing to render: unresolved placeholders {sorted(set(leftover))}")

out = Path("generated/odoo.conf")
out.write_text(src)
out.chmod(0o600)
print(f"Rendered {out} (0600)")
PY
