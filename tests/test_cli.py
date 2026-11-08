import tomllib

import pytest

from agent_migration_toolkit.cli import gap_main, timeline_main

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


@pytest.mark.parametrize(
    ("content", "needle"),
    [
        (None, "missing.toml"),
        ("[[sub_process]\n", "not valid TOML"),
        ('[[sub_process]]\ndepartment = "X"\n', "missing fields"),
        (b"\xff\xfe", "UTF-8"),
    ],
    ids=["missing-file", "bad-toml", "schema-error", "not-utf8"],
)
def test_gap_main_invalid_input_exits_1_with_one_line_error(tmp_path, capsys, content, needle):
    path = tmp_path / "missing.toml"
    if isinstance(content, bytes):
        path.write_bytes(content)
    elif content is not None:
        path.write_text(content, encoding="utf-8")
    assert gap_main([str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert captured.err.count("\n") == 1
    assert needle in captured.err


RAW = "https://raw.githubusercontent.com/roebi/dept-legal/main/process-table.toml"
LEGAL = TABLE.replace("Finance/Billing", "Legal/Compliance")


def _sources(tmp_path, *entries):
    (tmp_path / "finance.toml").write_text(TABLE, encoding="utf-8")
    path = tmp_path / "sources.toml"
    path.write_text("".join(f"[[department]]\n{e}\n" for e in entries), encoding="utf-8")
    return path


def _fetch_legal(url, timeout):
    return LEGAL


def test_timeline_main_all_departments_ok_exits_0(tmp_path, capsys):
    sources = _sources(
        tmp_path,
        'name = "Finance/Billing"\npath = "finance.toml"',
        f'name = "Legal/Compliance"\nurl = "{RAW}"',
    )
    assert timeline_main([str(sources)], fetcher=_fetch_legal) == 0
    result = tomllib.loads(capsys.readouterr().out)
    assert [d["name"] for d in result["department"]] == ["Finance/Billing", "Legal/Compliance"]
    assert "program" in result


def test_timeline_main_writes_output_file_and_passes_timeout(tmp_path, capsys):
    seen = []

    def fetcher(url, timeout):
        seen.append(timeout)
        return LEGAL

    sources = _sources(tmp_path, f'name = "Legal/Compliance"\nurl = "{RAW}"')
    out = tmp_path / "timeline.toml"
    assert timeline_main([str(sources), "-o", str(out), "--timeout", "2.5"], fetcher=fetcher) == 0
    assert seen == [2.5]
    assert capsys.readouterr().out == ""
    assert tomllib.loads(out.read_text(encoding="utf-8"))["department"]
