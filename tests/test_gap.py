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
