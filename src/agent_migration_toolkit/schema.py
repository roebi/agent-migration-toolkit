"""Process-table data contract: parsing and validation (R-SCHEMA)."""

from __future__ import annotations

import tomllib
from typing import Any


class ValidationError(ValueError):
    """Raised when a process table or source list breaks the contract."""


def parse_table(text: str) -> list[dict[str, Any]]:
    """Parse TOML text into the list of [[sub_process]] rows (R-SCHEMA-001)."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"not valid TOML: {exc}") from exc
    rows = data.get("sub_process")
    if not isinstance(rows, list):
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
    errors: list[str] = []
    names_by_department: dict[Any, set[Any]] = {}
    for row in rows:
        names_by_department.setdefault(row.get("department"), set()).add(row.get("sub_process"))
    seen: set[tuple[Any, Any]] = set()
    for index, row in enumerate(rows):
        key = (row.get("department"), row.get("sub_process"))
        if key in seen:
            errors.append(f"{_label(index, row)}: duplicate department and sub_process")
        seen.add(key)
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            errors.append(f"{_label(index, row)}: missing fields {missing}")
            continue
        for field, allowed in ENUM_FIELDS.items():
            if row[field] not in allowed:
                errors.append(f"{_label(index, row)}: invalid {field} {row[field]!r}")
        if "effort_days" in row and not _is_non_negative_number(row["effort_days"]):
            errors.append(
                f"{_label(index, row)}: effort_days must be a non-negative number,"
                f" got {row['effort_days']!r}"
            )
        if "depends_on" in row:
            known = names_by_department[row["department"]]
            errors.extend(
                f"{_label(index, row)}: {problem}"
                for problem in _depends_on_problems(row["depends_on"], known)
            )
    return errors


def _depends_on_problems(depends_on: Any, known: set[Any]) -> list[str]:
    if not isinstance(depends_on, list) or not all(isinstance(n, str) for n in depends_on):
        return [f"depends_on must be a list of sub_process names, got {depends_on!r}"]
    return [
        f"depends_on {name!r} is not a sub_process of the same department"
        for name in depends_on
        if name not in known
    ]


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0
