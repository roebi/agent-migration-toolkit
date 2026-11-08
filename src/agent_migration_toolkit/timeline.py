"""Critical path timeline per department and across the program (R-TIME)."""

from __future__ import annotations

from typing import Any

from agent_migration_toolkit.gap import compute_gaps


def schedule_department(department: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Schedule the gap rows of one department's validated table."""
    tasks = [
        {"sub_process": gap["sub_process"], "earliest_start": 0} for gap in compute_gaps(rows)
    ]
    return {"name": department, "task": tasks}
