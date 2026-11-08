"""Department source list and fetching of process tables (R-SRC)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit

from agent_migration_toolkit.schema import ValidationError, load_table, parse_toml

ALLOWED_HOST = "raw.githubusercontent.com"
DEFAULT_TIMEOUT = 10.0

Fetcher = Callable[[str, float], str]


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


@dataclass(frozen=True)
class Loaded:
    department: str
    rows: list[dict[str, Any]] | None = None
    error: str | None = None


def load_all(
    sources: list[Source],
    fetcher: Fetcher,
    base_dir: Path,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[Loaded]:
    """Load and validate every department's process table."""
    return [_load_one(source, fetcher, base_dir, timeout) for source in sources]


def _load_one(source: Source, fetcher: Fetcher, base_dir: Path, timeout: float) -> Loaded:
    try:
        rows = load_table(_read(source, fetcher, base_dir, timeout))
    except (TimeoutError, URLError) as exc:
        if isinstance(exc, TimeoutError) or isinstance(exc.reason, TimeoutError):
            return Loaded(source.department, error=f"timeout after {timeout} s")
        return Loaded(source.department, error=f"fetch failed: {exc.reason}")
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        return Loaded(source.department, error=str(exc))
    foreign = sorted({row["department"] for row in rows} - {source.department})
    if foreign:
        return Loaded(
            source.department,
            error=f"table contains department(s) {foreign}, expected {source.department!r}",
        )
    return Loaded(source.department, rows=rows)


def _read(source: Source, fetcher: Fetcher, base_dir: Path, timeout: float) -> str:
    if source.url is not None:
        return fetcher(source.url, timeout)
    return (base_dir / str(source.path)).read_text(encoding="utf-8")
