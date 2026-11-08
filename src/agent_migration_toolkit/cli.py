"""Command line entry points: thin wrappers over the pure core."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import tomli_w

from agent_migration_toolkit.gap import compute_gaps
from agent_migration_toolkit.schema import ValidationError, load_table
from agent_migration_toolkit.sources import (
    DEFAULT_TIMEOUT,
    Fetcher,
    load_all,
    parse_sources,
    urllib_fetcher,
)
from agent_migration_toolkit.timeline import build_timeline

USER_ERRORS = (ValidationError, OSError, UnicodeDecodeError)


def gap_main(argv: list[str] | None = None) -> int:
    """gap-analysis-creator: process table -> gap table (R-GAP-004)."""
    parser = argparse.ArgumentParser(
        prog="gap-analysis-creator", description="Create a gap table from a process table"
    )
    parser.add_argument("process_table", type=Path, help="path to process-table.toml")
    _add_output(parser)
    args = parser.parse_args(argv)
    try:
        rows = load_table(_read_text(args.process_table))
        _write({"gap": compute_gaps(rows)}, args.output)
    except USER_ERRORS as exc:
        return _fail(exc)
    return 0


def timeline_main(argv: list[str] | None = None, fetcher: Fetcher = urllib_fetcher) -> int:
    """critical-path-timeline: source list -> program timeline (R-TIME-009)."""
    parser = argparse.ArgumentParser(
        prog="critical-path-timeline",
        description="Build the critical path timeline across department process tables",
    )
    parser.add_argument("sources", type=Path, help="path to the department source list (TOML)")
    _add_output(parser)
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"seconds per fetch (default: {DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args(argv)
    sources = parse_sources(_read_text(args.sources))
    loaded = load_all(sources, fetcher=fetcher, base_dir=args.sources.parent, timeout=args.timeout)
    _write(build_timeline(loaded), args.output)
    return 0


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path}: not UTF-8 text") from exc


def _fail(exc: Exception) -> int:
    """Print a one-line error to stderr and return exit code 1 (NFR-03)."""
    message = " ".join(str(exc).split())
    sys.stderr.write(f"error: {message}\n")
    return 1


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
