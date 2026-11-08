"""Gap analysis: sub-processes whose interface is not yet an OpenAPI contract (R-GAP)."""

from __future__ import annotations

from typing import Any


def compute_gaps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one gap row per validated row whose interface_type is not openapi."""
    return [row for row in rows if row["interface_type"] != "openapi"]
