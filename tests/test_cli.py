import tomllib

import pytest

from agent_migration_toolkit.cli import gap_main

TABLE = """
[[sub_process]]
department = "Finance/Billing"
process = "Invoice run"
sub_process = "Match usage to contract"
automation_grade = "manual"
output_artifact = "match report"
interface_type = "manual"

[[sub_process]]
department = "Finance/Billing"
process = "Invoice run"
sub_process = "Send invoice"
automation_grade = "full"
output_artifact = "invoice"
interface_type = "openapi"
"""


@pytest.fixture
def table(tmp_path):
    path = tmp_path / "process-table.toml"
    path.write_text(TABLE, encoding="utf-8")
    return path


def test_gap_main_writes_gap_toml_to_stdout(table, capsys):
    assert gap_main([str(table)]) == 0
    gaps = tomllib.loads(capsys.readouterr().out)["gap"]
    assert [g["sub_process"] for g in gaps] == ["Match usage to contract"]


def test_gap_main_writes_to_output_file(table, tmp_path, capsys):
    out = tmp_path / "gaps.toml"
    assert gap_main([str(table), "-o", str(out)]) == 0
    assert capsys.readouterr().out == ""
    assert len(tomllib.loads(out.read_text(encoding="utf-8"))["gap"]) == 1
