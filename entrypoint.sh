#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -eq 0 ]; then
  exec pytest tools/tests -q
fi
exec "$@"
