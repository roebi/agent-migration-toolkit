"""Gap analysis creator.

Reads a department process table (YAML, following
schema/process-table.schema.yaml) and produces a gap table: one row
per sub-process whose interface to the next process is not yet a
clean OpenAPI contract.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS = {
    "department",
    "process",
    "sub_process",
    "automation_grade",
    "output_artifact",
    "interface_type",
}

VALID_GRADES = {"full", "partial", "manual"}
VALID_INTERFACE_TYPES = {"openapi", "file", "manual", "none"}


def load_process_table(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("process table must be a YAML list of sub-process entries")
    return data


def validate_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - row.keys()
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
        return errors
    grade = row.get("automation_grade")
    if grade not in VALID_GRADES:
        errors.append(f"invalid automation_grade: {grade!r}")
    itype = row.get("interface_type")
    if itype not in VALID_INTERFACE_TYPES:
        errors.append(f"invalid interface_type: {itype!r}")
    return errors


def _gap_description(row: dict[str, Any]) -> str:
    interface_type = row["interface_type"]
    if interface_type == "none":
        return "no artifact defined yet - needs artifact definition first"
    if interface_type == "manual":
        return "manual handoff - needs schema and an OpenAPI endpoint"
    if interface_type == "file":
        return "file-based handoff - needs an OpenAPI wrap or bridge"
    return "unclassified gap"


def compute_gaps(process_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one gap row per sub-process whose interface is not openapi-clean."""
    gaps: list[dict[str, Any]] = []
    for row in process_table:
        errors = validate_row(row)
        if errors:
            raise ValueError(f"invalid row {row.get('sub_process', '?')!r}: {errors}")
        if row["interface_type"] != "openapi":
            gaps.append(
                {
                    "department": row["department"],
                    "process": row["process"],
                    "sub_process": row["sub_process"],
                    "current_interface": row["interface_type"],
                    "gap": _gap_description(row),
                }
            )
    return gaps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a gap table from a process table")
    parser.add_argument("process_table", type=Path, help="path to process-table.yaml")
    parser.add_argument("-o", "--output", type=Path, default=None, help="output path (default: stdout)")
    args = parser.parse_args(argv)

    table = load_process_table(args.process_table)
    gaps = compute_gaps(table)
    output_yaml = yaml.dump(gaps, sort_keys=False, allow_unicode=True)

    if args.output:
        args.output.write_text(output_yaml, encoding="utf-8")
    else:
        print(output_yaml)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
