"""Process-table data contract: parsing and validation (R-SCHEMA)."""

from __future__ import annotations

import math
import tomllib
from typing import Any


class ValidationError(ValueError):
    """Raised when a process table or source list breaks the contract."""


def parse_toml(text: str) -> dict[str, Any]:
    """Parse TOML text, turning syntax errors into ValidationError."""
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"not valid TOML: {exc}") from exc


def parse_table(text: str) -> list[dict[str, Any]]:
    """Parse TOML text into the list of [[sub_process]] rows (R-SCHEMA-001)."""
    rows = parse_toml(text).get("sub_process")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValidationError("process table must contain a [[sub_process]] array of tables")
    return rows


REQUIRED_FIELDS = (
    "department",
    "process",
    "sub_process",
    "automation_grade",
    "output_artifact",
    "interface_type",
)

VALID_GRADES = ("full", "partial", "manual")
VALID_INTERFACE_TYPES = ("openapi", "file", "manual", "none")
ENUM_FIELDS = {"automation_grade": VALID_GRADES, "interface_type": VALID_INTERFACE_TYPES}


def _label(index: int, row: dict[str, Any]) -> str:
    return f"row {index + 1} ({row.get('department', '?')}/{row.get('sub_process', '?')})"


def validate_table(rows: list[dict[str, Any]]) -> list[str]:
    """Return every contract violation in the table, one message per problem."""
    names_by_department: dict[str, set[str]] = {}
    for row in rows:
        names_by_department.setdefault(_text(row, "department"), set()).add(
            _text(row, "sub_process")
        )
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        key = (_text(row, "department"), _text(row, "sub_process"))
        problems = ["duplicate department and sub_process"] if key in seen else []
        seen.add(key)
        problems += _row_problems(row, names_by_department[key[0]])
        errors.extend(f"{_label(index, row)}: {problem}" for problem in problems)
    return errors


def _text(row: dict[str, Any], field: str) -> str:
    """Hashable text form of a field, used for lookups before types are checked."""
    value = row.get(field)
    return value if isinstance(value, str) else repr(value)


def _row_problems(row: dict[str, Any], known: set[str]) -> list[str]:
    missing = [field for field in REQUIRED_FIELDS if field not in row]
    if missing:
        return [f"missing fields {missing}"]
    not_text = [field for field in REQUIRED_FIELDS if not isinstance(row[field], str)]
    if not_text:
        return [f"fields must be strings: {not_text}"]
    problems = [
        f"invalid {field} {row[field]!r}"
        for field, allowed in ENUM_FIELDS.items()
        if row[field] not in allowed
    ]
    if "effort_days" in row and not _is_non_negative_number(row["effort_days"]):
        problems.append(f"effort_days must be a finite non-negative number, got {row['effort_days']!r}")
    if "depends_on" in row:
        problems += _depends_on_problems(row["depends_on"], known)
    return problems


def _depends_on_problems(depends_on: Any, known: set[str]) -> list[str]:
    if not isinstance(depends_on, list) or not all(isinstance(n, str) for n in depends_on):
        return [f"depends_on must be a list of sub_process names, got {depends_on!r}"]
    return [
        f"depends_on {name!r} is not a sub_process of the same department"
        for name in depends_on
        if name not in known
    ]


def _is_non_negative_number(value: Any) -> bool:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    return math.isfinite(value) and value >= 0


def load_table(text: str) -> list[dict[str, Any]]:
    """Parse and validate a process table; raise ValidationError listing every problem."""
    rows = parse_table(text)
    errors = validate_table(rows)
    if errors:
        raise ValidationError("; ".join(errors))
    return rows
