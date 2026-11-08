"""Command line entry points: thin wrappers over the pure core."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, NoReturn

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
EXIT_ERROR = 1
EXIT_PARTIAL = 2


class _Parser(argparse.ArgumentParser):
    """argparse exits with 2 on bad arguments; use 1 so 2 only means a partial timeline."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f"error: {message}\n")


def gap_main(argv: list[str] | None = None) -> int:
    """gap-analysis-creator: process table -> gap table (R-GAP-004)."""
    parser = _Parser(
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
    parser = _Parser(
        prog="critical-path-timeline",
        description="Build the critical path timeline across department process tables",
    )
    parser.add_argument("sources", type=Path, help="path to the department source list (TOML)")
    _add_output(parser)
    parser.add_argument(
        "--timeout",
        type=_positive_seconds,
        default=DEFAULT_TIMEOUT,
        help=f"seconds per fetch (default: {DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args(argv)
    try:
        sources = parse_sources(_read_text(args.sources))
        loaded = load_all(
            sources, fetcher=fetcher, base_dir=args.sources.parent, timeout=args.timeout
        )
        timeline = build_timeline(loaded)
        if not timeline["department"]:
            raise ValidationError(f"no department could be processed: {_reasons(timeline)}")
        _write(timeline, args.output)
    except USER_ERRORS as exc:
        return _fail(exc)
    for failure in timeline["failure"]:
        sys.stderr.write(f"warning: {failure['department']}: {failure['reason']}\n")
    return EXIT_PARTIAL if timeline["failure"] else 0


def _positive_seconds(text: str) -> float:
    value = float(text)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive number of seconds, got {text!r}")
    return value


def _reasons(timeline: dict[str, Any]) -> str:
    return "; ".join(f"{f['department']}: {f['reason']}" for f in timeline["failure"]) or "none"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path}: not UTF-8 text") from exc


def _fail(exc: Exception) -> int:
    """Print a one-line error to stderr and return exit code 1 (NFR-03)."""
    message = " ".join(str(exc).split())
    sys.stderr.write(f"error: {message}\n")
    return EXIT_ERROR


def _add_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o", "--output", type=Path, default=None, help="output path (default: stdout)"
    )


def _write(data: dict[str, Any], output: Path | None) -> None:
    text = tomli_w.dumps(data)
    if output is None:
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        output.write_text(text, encoding="utf-8")
