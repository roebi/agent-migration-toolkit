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


def _label(index: int, row: dict[str, Any]) -> str:
    return f"row {index + 1} ({row.get('department', '?')}/{row.get('sub_process', '?')})"


def validate_table(rows: list[dict[str, Any]]) -> list[str]:
    """Return every contract violation in the table, one message per problem."""
    errors: list[str] = []
    for index, row in enumerate(rows):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            errors.append(f"{_label(index, row)}: missing fields {missing}")
    return errors
