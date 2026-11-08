"""Department source list and fetching of process tables (R-SRC)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_migration_toolkit.schema import ValidationError, parse_toml


@dataclass(frozen=True)
class Source:
    department: str
    url: str | None = None
    path: str | None = None


def parse_sources(text: str) -> list[Source]:
    """Parse the TOML source list into one Source per [[department]] entry (R-SRC-001)."""
    entries = parse_toml(text).get("department")
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise ValidationError("source list must contain a [[department]] array of tables")
    return [_source(index, entry) for index, entry in enumerate(entries)]


def _source(index: int, entry: dict[str, Any]) -> Source:
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        raise ValidationError(f"source entry {index + 1}: missing name")
    return Source(name, url=entry.get("url"), path=entry.get("path"))
