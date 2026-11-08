#!/usr/bin/env bash
# No arguments: run the test suite. Otherwise run the given command,
# e.g. gap-analysis-creator or critical-path-timeline.
set -euo pipefail
if [ "$#" -eq 0 ]; then
  exec pytest -q
fi
exec "$@"
