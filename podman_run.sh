#!/usr/bin/env bash
set -euo pipefail
IMAGE_NAME="agent-migration-toolkit"
IMAGE_TAG="latest"
cd "$(dirname "$0")"
podman run --rm -it \
  -v "$(pwd)/src:/app/src:z" \
  -v "$(pwd)/tests:/app/tests:z" \
  -v "$(pwd)/schema:/app/schema:z" \
  "${IMAGE_NAME}:${IMAGE_TAG}" "$@"
