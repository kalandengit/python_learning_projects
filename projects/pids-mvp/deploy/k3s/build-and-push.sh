#!/usr/bin/env bash
# Build & push the multi-arch (arm64 + amd64) PIDS backend image the k3s manifests reference.
# Requires Docker Buildx. Run from the repo root or anywhere — paths are resolved relative here.
#
#   REGISTRY=ghcr.io/<owner> ./deploy/k3s/build-and-push.sh
#
set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/kalandengit}"
IMAGE="${REGISTRY}/pids-backend"
TAG="${TAG:-latest}"
CONTEXT="$(cd "$(dirname "$0")/../../backend" && pwd)"

echo "Building ${IMAGE}:${TAG} (linux/amd64,linux/arm64) from ${CONTEXT}"

docker buildx create --use --name pids-builder >/dev/null 2>&1 || docker buildx use pids-builder

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "${IMAGE}:${TAG}" \
  --push \
  "${CONTEXT}"

echo "Pushed ${IMAGE}:${TAG}. Update deploy/k3s/pids.yaml image if REGISTRY differs."
