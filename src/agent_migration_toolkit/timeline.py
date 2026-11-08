"""Critical path timeline per department and across the program (R-TIME)."""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from typing import Any

from agent_migration_toolkit.gap import compute_gaps
from agent_migration_toolkit.schema import ValidationError

GAP_FIELDS = ("process", "sub_process", "current_interface")
TOLERANCE = 1e-9
QUICK_RAMP_SHARE = 0.2


def find_cycle(rows: list[dict[str, Any]]) -> list[str] | None:
    """Return the sub_process names of one depends_on cycle, or None (R-TIME-008)."""
    graph = {row["sub_process"]: row.get("depends_on", []) for row in rows}
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as exc:
        return exc.args[1]
    return None


def schedule_department(department: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Schedule the gap rows of one department's validated table."""
    cycle = find_cycle(rows)
    if cycle:
        raise ValidationError(f"depends_on cycle: {' -> '.join(cycle)}")
    gaps = compute_gaps(rows)
    estimated = {gap["sub_process"]: gap for gap in gaps if "effort_days" in gap}
    unestimated = [gap for gap in gaps if "effort_days" not in gap]
    tasks, length = _schedule(estimated, {gap["sub_process"] for gap in unestimated})
    critical = sorted((t for t in tasks if t["critical"]), key=lambda t: t["earliest_start"])
    return {
        "name": department,
        "critical_path_days": length,
        "critical_path": [t["sub_process"] for t in critical],
        "task": tasks,
        "unestimated": [_pick(gap) for gap in unestimated],
    }


def _pick(gap: dict[str, Any]) -> dict[str, Any]:
    return {key: gap[key] for key in GAP_FIELDS}


def _schedule(
    gaps: dict[str, dict[str, Any]], unestimated: set[str]
) -> tuple[list[dict[str, Any]], float]:
    """Critical path method over tasks; predecessors that are not tasks are ignored."""
    preds = {
        name: [p for p in gap.get("depends_on", []) if p in gaps] for name, gap in gaps.items()
    }
    order = list(TopologicalSorter(preds).static_order())

    start: dict[str, float] = {}
    finish: dict[str, float] = {}
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

    tasks = []
    for name, gap in gaps.items():
        slack = latest_start[name] - start[name]
        critical = abs(slack) < TOLERANCE
        tasks.append(
            {
                **_pick(gap),
                "effort_days": gap["effort_days"],
                "earliest_start": start[name],
                "earliest_finish": finish[name],
                "slack_days": 0 if critical else slack,
                "critical": critical,
                "block": _block(start[name], length),
                "waits_on_unestimated": [
                    p for p in gap.get("depends_on", []) if p in unestimated
                ],
            }
        )
    return tasks, length


def _block(earliest_start: float, length: float) -> str:
    if length == 0 or earliest_start < QUICK_RAMP_SHARE * length - TOLERANCE:
        return "quick_ramp"
    return "hardening"
