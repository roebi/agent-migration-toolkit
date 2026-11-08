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
