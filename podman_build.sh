#!/usr/bin/env bash
set -euo pipefail
IMAGE_NAME="agentifizierung-toolkit"
IMAGE_TAG="latest"
cd "$(dirname "$0")"
podman build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
