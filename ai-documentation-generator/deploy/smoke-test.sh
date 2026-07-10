#!/usr/bin/env bash
#
# smoke-test.sh — quick post-deploy health check. Verifies containers are up and
# the app answers over HTTP through Caddy. Exits non-zero on failure.
#
#   ./smoke-test.sh            # tests http://localhost
#   BASE=http://172.236.240.38 ./smoke-test.sh
set -uo pipefail
cd "$(dirname "$0")"

BASE="${BASE:-http://localhost}"
fail=0

echo "==> Containers"
docker compose ps || fail=1

check() { # <path> <expected-codes-regex> <label>
  local path="$1" want="$2" label="$3" code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${BASE}${path}" || echo 000)"
  if [[ "$code" =~ $want ]]; then
    echo "  ok   ${label} (${path}) -> ${code}"
  else
    echo "  FAIL ${label} (${path}) -> ${code} (wanted ${want})"; fail=1
  fi
}

echo "==> HTTP routes on ${BASE}"
check "/"        '^(200|307|308)$' "home"
check "/pricing" '^(200|307|308)$' "pricing"
check "/login"   '^(200|307|308)$' "login"
# Protected route should redirect unauthenticated users (302/307) rather than 200/500.
check "/dashboard" '^(302|307|308|401)$' "dashboard-redirect"

echo "==> Worker process"
if docker compose ps worker | grep -qi 'up\|running'; then
  echo "  ok   worker container running"
else
  echo "  FAIL worker container not running"; fail=1
fi

echo
if [[ "$fail" -eq 0 ]]; then
  echo "SMOKE TEST PASSED"
else
  echo "SMOKE TEST FAILED — inspect: docker compose logs -f web worker"
fi
exit "$fail"
