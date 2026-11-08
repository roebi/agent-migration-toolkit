"""Command line entry points: thin wrappers over the pure core."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import tomli_w

from agent_migration_toolkit.gap import compute_gaps
from agent_migration_toolkit.schema import load_table


def gap_main(argv: list[str] | None = None) -> int:
    """gap-analysis-creator: process table -> gap table (R-GAP-004)."""
    parser = argparse.ArgumentParser(
        prog="gap-analysis-creator", description="Create a gap table from a process table"
    )
    parser.add_argument("process_table", type=Path, help="path to process-table.toml")
    _add_output(parser)
    args = parser.parse_args(argv)
    rows = load_table(args.process_table.read_text(encoding="utf-8"))
    _write({"gap": compute_gaps(rows)}, args.output)
    return 0


def _add_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o", "--output", type=Path, default=None, help="output path (default: stdout)"
    )


def _write(data: dict[str, Any], output: Path | None) -> None:
    text = tomli_w.dumps(data)
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text, encoding="utf-8")
