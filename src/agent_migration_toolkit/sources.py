"""Department source list and fetching of process tables (R-SRC)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from agent_migration_toolkit.schema import ValidationError, parse_toml

ALLOWED_HOST = "raw.githubusercontent.com"


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
    url, path = entry.get("url"), entry.get("path")
    if (url is None) == (path is None):
        raise ValidationError(f"source {name!r}: needs exactly one of url or path")
    if url is not None and not _is_allowed_url(url):
        raise ValidationError(f"source {name!r}: url must be https://{ALLOWED_HOST}/...")
    return Source(name, url=url, path=path)


def _is_allowed_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname == ALLOWED_HOST
