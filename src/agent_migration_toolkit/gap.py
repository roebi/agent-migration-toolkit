"""Gap analysis: sub-processes whose interface is not yet an OpenAPI contract (R-GAP)."""

from __future__ import annotations

from typing import Any

GAP_DESCRIPTIONS = {
    "none": "no artifact defined yet - needs artifact definition first",
    "manual": "manual handoff - needs schema and an OpenAPI endpoint",
    "file": "file-based handoff - needs an OpenAPI wrap or bridge",
}
CARRIED_FIELDS = ("effort_days", "depends_on")


def compute_gaps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one gap row per validated row whose interface_type is not openapi."""
    return [_gap_row(row) for row in rows if row["interface_type"] != "openapi"]


def _gap_row(row: dict[str, Any]) -> dict[str, Any]:
    gap = {
        "department": row["department"],
        "process": row["process"],
        "sub_process": row["sub_process"],
        "current_interface": row["interface_type"],
        "gap": GAP_DESCRIPTIONS[row["interface_type"]],
    }
    gap.update({field: row[field] for field in CARRIED_FIELDS if field in row})
    return gap
