#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -eq 0 ]; then
  exec uv run pytest -q
fi
exec "$@"
