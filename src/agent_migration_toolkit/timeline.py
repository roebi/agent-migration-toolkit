"""Critical path timeline per department and across the program (R-TIME)."""

from __future__ import annotations

from graphlib import TopologicalSorter
from typing import Any

from agent_migration_toolkit.gap import compute_gaps

GAP_FIELDS = ("process", "sub_process", "current_interface")


def schedule_department(department: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Schedule the gap rows of one department's validated table."""
    gaps = compute_gaps(rows)
    estimated = {gap["sub_process"]: gap for gap in gaps if "effort_days" in gap}
    unestimated = [_pick(gap) for gap in gaps if "effort_days" not in gap]
    return {"name": department, "task": _schedule(estimated), "unestimated": unestimated}


def _pick(gap: dict[str, Any]) -> dict[str, Any]:
    return {key: gap[key] for key in GAP_FIELDS}


def _schedule(gaps: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Critical path method over tasks; predecessors that are not tasks are ignored."""
    preds = {
        name: [p for p in gap.get("depends_on", []) if p in gaps] for name, gap in gaps.items()
    }
    order = list(TopologicalSorter(preds).static_order())

    finish: dict[str, float] = {}
    start: dict[str, float] = {}
    for name in order:
        start[name] = max((finish[p] for p in preds[name]), default=0)
        finish[name] = start[name] + gaps[name]["effort_days"]
    length = max(finish.values(), default=0)

    succs: dict[str, list[str]] = {name: [] for name in gaps}
    for name, names in preds.items():
        for pred in names:
            succs[pred].append(name)
    latest_start: dict[str, float] = {}
    for name in reversed(order):
        latest_finish = min((latest_start[s] for s in succs[name]), default=length)
        latest_start[name] = latest_finish - gaps[name]["effort_days"]

    return [
        {
            **_pick(gap),
            "effort_days": gap["effort_days"],
            "earliest_start": start[name],
            "earliest_finish": finish[name],
            "slack_days": latest_start[name] - start[name],
        }
        for name, gap in gaps.items()
    ]
