import pytest

from agent_migration_toolkit.gap import compute_gaps


def test_openapi_row_produces_no_gap(row):
    assert compute_gaps([row(interface_type="openapi")]) == []


@pytest.mark.parametrize("itype", ["file", "manual", "none"])
def test_non_openapi_row_produces_one_gap(row, itype):
    assert len(compute_gaps([row(interface_type=itype)])) == 1


def test_mixed_table_only_flags_non_openapi_rows(row):
    rows = [row(sub_process="A", interface_type="openapi"), row(sub_process="B")]
    assert [g["sub_process"] for g in compute_gaps(rows)] == ["B"]


def test_gap_row_has_department_process_sub_process_interface_and_gap(row):
    [gap] = compute_gaps([row(notes="drop me", automation_grade="partial")])
    assert gap["department"] == "Finance/Billing"
    assert gap["process"] == "Invoice run"
    assert gap["sub_process"] == "Match usage to contract"
    assert gap["current_interface"] == "manual"
    assert isinstance(gap["gap"], str) and gap["gap"]
    assert "notes" not in gap and "automation_grade" not in gap


def test_gap_row_carries_effort_and_depends_on_when_present(row):
    [plain, planned] = compute_gaps(
        [row(sub_process="A"), row(sub_process="B", effort_days=3, depends_on=["A"])]
    )
    assert "effort_days" not in plain and "depends_on" not in plain
    assert planned["effort_days"] == 3 and planned["depends_on"] == ["A"]


@pytest.mark.parametrize(
    ("itype", "needle"),
    [("none", "artifact definition"), ("manual", "OpenAPI endpoint"), ("file", "bridge")],
)
def test_gap_description_names_next_step_per_interface_type(row, itype, needle):
    [gap] = compute_gaps([row(interface_type=itype)])
    assert needle in gap["gap"]
