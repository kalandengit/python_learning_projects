#!/usr/bin/env bash
# Smoke probe used by CD (Section 12.2): waits until the target environment
# serves the expected image tag, then checks liveness/readiness.
set -euo pipefail

BASE_URL="${1:?usage: smoke.sh <base-url> <expected-tag>}"
EXPECTED_TAG="${2:?usage: smoke.sh <base-url> <expected-tag>}"
DEADLINE=$((SECONDS + 600))

echo "Waiting for ${BASE_URL} to serve ${EXPECTED_TAG} ..."
while (( SECONDS < DEADLINE )); do
  live=$(curl -fsS -o /dev/null -w '%{http_code}' "${BASE_URL}/healthz/live" || true)
  ready=$(curl -fsS -o /dev/null -w '%{http_code}' "${BASE_URL}/healthz/ready" || true)
  version=$(curl -fsS "${BASE_URL}/healthz/version" 2>/dev/null || echo "unknown")

  if [[ "$live" == "200" && "$ready" == "200" && "$version" == *"$EXPECTED_TAG"* ]]; then
    echo "Smoke OK: live=200 ready=200 version=${version}"
    exit 0
  fi
  echo "  live=${live} ready=${ready} version=${version}; retrying in 10s"
  sleep 10
done

echo "Smoke FAILED: ${EXPECTED_TAG} not healthy within 10 minutes" >&2
exit 1

# VERIFY: /healthz/version endpoint returning the image tag needs to be added to the service (one MapGet reading an env var set from the image tag).
