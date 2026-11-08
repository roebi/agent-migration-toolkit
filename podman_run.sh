#!/usr/bin/env bash
set -euo pipefail
IMAGE_NAME="agent-migration-toolkit"
IMAGE_TAG="latest"
cd "$(dirname "$0")"
podman run --rm -it \
  -v "$(pwd)/src:/app/src:Z" \
  -v "$(pwd)/tests:/app/tests:Z" \
  -v "$(pwd)/schema:/app/schema:Z" \
  "${IMAGE_NAME}:${IMAGE_TAG}" "$@"
