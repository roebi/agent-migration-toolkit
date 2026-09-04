#!/usr/bin/env bash
set -euo pipefail
IMAGE_NAME="agentifizierung-toolkit"
IMAGE_TAG="latest"
cd "$(dirname "$0")"
podman run --rm -it \
  -v "$(pwd)/tools:/app/tools:Z" \
  -v "$(pwd)/schema:/app/schema:Z" \
  "${IMAGE_NAME}:${IMAGE_TAG}" "$@"
