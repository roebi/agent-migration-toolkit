import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gap_analysis_creator import compute_gaps, validate_row  # noqa: E402


def _row(**overrides):
    base = {
        "department": "Engineering/Dev-Ops",
        "process": "Release",
        "sub_process": "Run test suite",
        "automation_grade": "full",
        "output_artifact": "test_report.json",
        "interface_type": "openapi",
    }
    base.update(overrides)
    return base


def test_openapi_row_produces_no_gap():
    table = [_row()]
    assert compute_gaps(table) == []


def test_manual_row_produces_gap_with_reason():
    table = [_row(
        department="Finance/Billing",
        process="Invoice run",
        sub_process="Match usage to contract",
        automation_grade="manual",
        output_artifact="match_report.xlsx",
        interface_type="manual",
    )]
    gaps = compute_gaps(table)
    assert len(gaps) == 1
    assert gaps[0]["sub_process"] == "Match usage to contract"
    assert "schema" in gaps[0]["gap"]


def test_file_row_produces_bridge_gap():
    table = [_row(interface_type="file", output_artifact="report.csv")]
    gaps = compute_gaps(table)
    assert len(gaps) == 1
    assert "bridge" in gaps[0]["gap"] or "wrap" in gaps[0]["gap"]


def test_none_interface_produces_artifact_gap():
    table = [_row(interface_type="none")]
    gaps = compute_gaps(table)
    assert len(gaps) == 1
    assert "artifact" in gaps[0]["gap"]


def test_mixed_table_only_flags_non_openapi_rows():
    table = [
        _row(sub_process="Run test suite", interface_type="openapi"),
        _row(sub_process="Match usage to contract", interface_type="manual"),
    ]
    gaps = compute_gaps(table)
    assert len(gaps) == 1
    assert gaps[0]["sub_process"] == "Match usage to contract"


def test_missing_required_field_raises():
    with pytest.raises(ValueError):
        compute_gaps([{"department": "Legal/Compliance"}])


def test_invalid_automation_grade_raises():
    table = [_row(automation_grade="mostly")]
    with pytest.raises(ValueError):
        compute_gaps(table)


def test_invalid_interface_type_raises():
    table = [_row(interface_type="carrier_pigeon")]
    with pytest.raises(ValueError):
        compute_gaps(table)


def test_validate_row_reports_missing_fields():
    errors = validate_row({"department": "X"})
    assert any("missing fields" in e for e in errors)


def test_validate_row_passes_on_valid_row():
    assert validate_row(_row()) == []
