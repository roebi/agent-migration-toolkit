import pytest

from agent_migration_toolkit.schema import ValidationError
from agent_migration_toolkit.sources import Loaded
from agent_migration_toolkit.timeline import build_timeline, find_cycle, schedule_department


def _names(items):
    return [item["sub_process"] for item in items]


def test_schedule_only_includes_gap_rows(row):
    rows = [
        row(sub_process="Done", interface_type="openapi", effort_days=4),
        row(sub_process="Gap", effort_days=2, depends_on=["Done"]),
    ]
    result = schedule_department("Finance/Billing", rows)
    assert _names(result["task"]) == ["Gap"]
    assert result["task"][0]["earliest_start"] == 0


def test_gap_without_effort_is_unestimated_and_not_scheduled(row):
    rows = [row(sub_process="Known", effort_days=1), row(sub_process="Unknown")]
    result = schedule_department("Finance/Billing", rows)
    assert _names(result["task"]) == ["Known"]
    assert _names(result["unestimated"]) == ["Unknown"]
    assert result["unestimated"][0]["current_interface"] == "manual"


def _by_name(result):
    return {task["sub_process"]: task for task in result["task"]}


def test_forward_and_backward_pass_compute_start_finish_and_slack(row):
    # A(3) -> C(2); B(1) -> C ; D(1) independent
    rows = [
        row(sub_process="A", effort_days=3),
        row(sub_process="B", effort_days=1),
        row(sub_process="C", effort_days=2, depends_on=["A", "B"]),
        row(sub_process="D", effort_days=1),
    ]
    tasks = _by_name(schedule_department("Finance/Billing", rows))
    assert (tasks["A"]["earliest_start"], tasks["A"]["earliest_finish"]) == (0, 3)
    assert (tasks["C"]["earliest_start"], tasks["C"]["earliest_finish"]) == (3, 5)
    assert tasks["A"]["slack_days"] == 0
    assert tasks["B"]["slack_days"] == 2
    assert tasks["C"]["slack_days"] == 0
    assert tasks["D"]["slack_days"] == 4


def test_task_output_has_process_interface_and_effort(row):
    [task] = schedule_department("Finance/Billing", [row(effort_days=2.5)])["task"]
    assert task["process"] == "Invoice run"
    assert task["current_interface"] == "manual"
    assert task["effort_days"] == 2.5


def test_tasks_are_scheduled_regardless_of_row_order(row):
    rows = [
        row(sub_process="Late", effort_days=1, depends_on=["Early"]),
        row(sub_process="Early", effort_days=2),
    ]
    tasks = _by_name(schedule_department("Finance/Billing", rows))
    assert tasks["Late"]["earliest_start"] == 2


def _diamond(row):
    # A(3) -> C(2); B(1) -> C ; D(1) independent  => critical A, C ; length 5
    return [
        row(sub_process="A", effort_days=3),
        row(sub_process="B", effort_days=1),
        row(sub_process="C", effort_days=2, depends_on=["A", "B"]),
        row(sub_process="D", effort_days=1),
    ]


def test_zero_slack_tasks_form_critical_path_with_length(row):
    result = schedule_department("Finance/Billing", _diamond(row))
    tasks = _by_name(result)
    assert [n for n, t in tasks.items() if t["critical"]] == ["A", "C"]
    assert result["critical_path"] == ["A", "C"]
    assert result["critical_path_days"] == 5


def test_critical_path_uses_float_tolerance(row):
    rows = [
        row(sub_process="A", effort_days=0.1),
        row(sub_process="B", effort_days=0.2, depends_on=["A"]),
        row(sub_process="C", effort_days=0.25),
    ]
    result = schedule_department("Finance/Billing", rows)
    assert result["critical_path"] == ["A", "B"]


def test_empty_department_has_zero_length(row):
    result = schedule_department("Finance/Billing", [row(interface_type="openapi")])
    assert result["critical_path"] == [] and result["critical_path_days"] == 0


def test_block_is_quick_ramp_in_first_20_percent_else_hardening(row):
    # chain A(1) -> B(4) -> C(5): length 10, quick ramp = start < 2
    rows = [
        row(sub_process="A", effort_days=1),
        row(sub_process="B", effort_days=4, depends_on=["A"]),
        row(sub_process="C", effort_days=5, depends_on=["B"]),
    ]
    tasks = _by_name(schedule_department("Finance/Billing", rows))
    assert tasks["A"]["block"] == "quick_ramp"
    assert tasks["B"]["block"] == "quick_ramp"  # starts at 1 < 2
    assert tasks["C"]["block"] == "hardening"  # starts at 5


def test_block_at_exact_20_percent_is_hardening(row):
    rows = [
        row(sub_process="A", effort_days=2),
        row(sub_process="B", effort_days=8, depends_on=["A"]),
    ]
    assert _by_name(schedule_department("Finance/Billing", rows))["B"]["block"] == "hardening"


def test_block_for_zero_length_department_is_quick_ramp(row):
    [task] = schedule_department("Finance/Billing", [row(effort_days=0)])["task"]
    assert task["block"] == "quick_ramp"


def test_task_lists_unestimated_gap_predecessors(row):
    rows = [
        row(sub_process="Unknown"),
        row(sub_process="Done", interface_type="openapi"),
        row(sub_process="Next", effort_days=1, depends_on=["Unknown", "Done"]),
    ]
    [task] = schedule_department("Finance/Billing", rows)["task"]
    assert task["waits_on_unestimated"] == ["Unknown"]
    assert task["earliest_start"] == 0


def test_near_zero_slack_is_reported_as_zero(row):
    rows = [
        row(sub_process="A", effort_days=0.1),
        row(sub_process="B", effort_days=0.2, depends_on=["A"]),
    ]
    assert all(t["slack_days"] == 0 for t in schedule_department("D", rows)["task"])


def test_cycle_in_depends_on_is_rejected_with_names(row):
    rows = [
        row(sub_process="A", effort_days=1, depends_on=["C"]),
        row(sub_process="B", effort_days=1, depends_on=["A"]),
        row(sub_process="C", interface_type="openapi", depends_on=["B"]),
    ]
    with pytest.raises(ValidationError, match="cycle") as excinfo:
        schedule_department("Finance/Billing", rows)
    assert all(name in str(excinfo.value) for name in "ABC")


def test_find_cycle_returns_none_for_acyclic_table(row):
    rows = [row(sub_process="A"), row(sub_process="B", depends_on=["A"])]
    assert find_cycle(rows) is None


def _dept(row, department, *efforts):
    return [
        row(department=department, sub_process=f"S{i}", effort_days=e)
        for i, e in enumerate(efforts)
    ]


def test_build_timeline_schedules_each_department_and_lists_failures(row):
    loaded = [
        Loaded("Finance/Billing", rows=_dept(row, "Finance/Billing", 3)),
        Loaded("Legal/Compliance", error="timeout after 10.0 s"),
    ]
    result = build_timeline(loaded)
    assert [d["name"] for d in result["department"]] == ["Finance/Billing"]
    assert result["failure"] == [
        {"department": "Legal/Compliance", "reason": "timeout after 10.0 s"}
    ]


def test_build_timeline_reports_cycle_as_department_failure(row):
    rows = [
        row(sub_process="A", depends_on=["B"]),
        row(sub_process="B", depends_on=["A"]),
    ]
    result = build_timeline([Loaded("Finance/Billing", rows=rows)])
    assert result["department"] == []
    assert "cycle" in result["failure"][0]["reason"]


def test_build_timeline_program_is_longest_department_first_on_tie(row):
    loaded = [
        Loaded("Product/QA", rows=_dept(row, "Product/QA", 4)),
        Loaded("Finance/Billing", rows=_dept(row, "Finance/Billing", 7)),
        Loaded("Legal/Compliance", rows=_dept(row, "Legal/Compliance", 7)),
    ]
    assert build_timeline(loaded)["program"] == {
        "length_days": 7,
        "critical_department": "Finance/Billing",
    }


def test_build_timeline_program_without_departments_is_empty():
    result = build_timeline([Loaded("Finance/Billing", error="boom")])
    assert result["program"] == {"length_days": 0, "critical_department": ""}
