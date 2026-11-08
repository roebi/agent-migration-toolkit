import io
from urllib.error import URLError

import pytest

from agent_migration_toolkit import sources
from agent_migration_toolkit.schema import ValidationError
from agent_migration_toolkit.sources import Source, load_all, parse_sources

RAW = "https://raw.githubusercontent.com/roebi/dept-finance/main/process-table.toml"


def test_parse_sources_reads_url_and_path_entries():
    text = (
        f'[[department]]\nname = "Finance/Billing"\nurl = "{RAW}"\n\n'
        '[[department]]\nname = "Legal/Compliance"\npath = "legal.toml"\n'
    )
    assert parse_sources(text) == [
        Source("Finance/Billing", url=RAW, path=None),
        Source("Legal/Compliance", url=None, path="legal.toml"),
    ]


def test_parse_sources_without_department_array_raises():
    with pytest.raises(ValidationError, match=r"\[\[department\]\]"):
        parse_sources('x = 1\n')


def test_parse_sources_entry_without_name_raises():
    with pytest.raises(ValidationError, match="name"):
        parse_sources('[[department]]\npath = "a.toml"\n')


@pytest.mark.parametrize(
    "fields",
    [f'url = "{RAW}"\npath = "a.toml"\n', ""],
    ids=["both", "neither"],
)
def test_parse_sources_requires_exactly_one_of_url_and_path(fields):
    with pytest.raises(ValidationError, match="Finance/Billing.*exactly one of url or path"):
        parse_sources(f'[[department]]\nname = "Finance/Billing"\n{fields}')


@pytest.mark.parametrize(
    "url",
    [
        "http://raw.githubusercontent.com/roebi/x/main/t.toml",
        "https://example.com/t.toml",
        "https://raw.githubusercontent.com.evil.io/t.toml",
        "file:///etc/passwd",
    ],
)
def test_parse_sources_rejects_url_outside_https_raw_github(url):
    with pytest.raises(ValidationError, match="raw.githubusercontent.com"):
        parse_sources(f'[[department]]\nname = "D"\nurl = "{url}"\n')


def _table(department="Legal/Compliance", sub_process="Review contract"):
    return (
        f'[[sub_process]]\ndepartment = "{department}"\nprocess = "P"\n'
        f'sub_process = "{sub_process}"\nautomation_grade = "manual"\n'
        'output_artifact = "o"\ninterface_type = "manual"\n'
    )


def _no_network(url, timeout):
    raise AssertionError("fetcher must not be called for path sources")


def test_load_all_reads_path_relative_to_base_dir(tmp_path):
    (tmp_path / "legal.toml").write_text(_table(), encoding="utf-8")
    sources = [Source("Legal/Compliance", path="legal.toml")]
    [loaded] = load_all(sources, fetcher=_no_network, base_dir=tmp_path)
    assert loaded.error is None
    assert loaded.department == "Legal/Compliance"
    assert loaded.rows[0]["sub_process"] == "Review contract"


def test_load_all_fetches_url_with_timeout(tmp_path):
    calls = []

    def fetcher(url, timeout):
        calls.append((url, timeout))
        return _table(department="Finance/Billing")

    [loaded] = load_all(
        [Source("Finance/Billing", url=RAW)], fetcher=fetcher, base_dir=tmp_path, timeout=3.0
    )
    assert calls == [(RAW, 3.0)]
    assert loaded.error is None and len(loaded.rows) == 1


def test_load_all_reports_timeout_as_department_failure(tmp_path):
    def fetcher(url, timeout):
        raise TimeoutError("timed out")

    [loaded] = load_all([Source("Finance/Billing", url=RAW)], fetcher=fetcher, base_dir=tmp_path)
    assert loaded.rows is None
    assert loaded.error == "timeout after 10.0 s"


def test_load_all_continues_after_failures_and_lists_reasons(tmp_path):
    (tmp_path / "bad.toml").write_text("[[sub_process]\n", encoding="utf-8")

    def fetcher(url, timeout):
        return _table(department="Finance/Billing")

    sources = [
        Source("Legal/Compliance", path="missing.toml"),
        Source("Product/QA", path="bad.toml"),
        Source("Finance/Billing", url=RAW),
    ]
    missing, bad, ok = load_all(sources, fetcher=fetcher, base_dir=tmp_path)
    assert "missing.toml" in missing.error
    assert "not valid TOML" in bad.error
    assert ok.error is None and ok.rows


def test_load_all_reports_network_error_as_failure(tmp_path):
    def fetcher(url, timeout):
        raise URLError("404 Not Found")

    [loaded] = load_all([Source("Finance/Billing", url=RAW)], fetcher=fetcher, base_dir=tmp_path)
    assert "404" in loaded.error


def test_load_all_reports_url_error_caused_by_timeout_as_timeout(tmp_path):
    def fetcher(url, timeout):
        raise URLError(TimeoutError("timed out"))

    [loaded] = load_all([Source("Finance/Billing", url=RAW)], fetcher=fetcher, base_dir=tmp_path)
    assert loaded.error == "timeout after 10.0 s"


def test_load_all_rejects_table_of_other_department(tmp_path):
    (tmp_path / "legal.toml").write_text(_table(department="Product/QA"), encoding="utf-8")
    [loaded] = load_all(
        [Source("Legal/Compliance", path="legal.toml")], fetcher=_no_network, base_dir=tmp_path
    )
    assert loaded.rows is None
    assert "Product/QA" in loaded.error and "Legal/Compliance" in loaded.error


def test_urllib_fetcher_returns_decoded_body_and_passes_timeout(monkeypatch):
    seen = {}

    def fake_urlopen(url, timeout):
        seen["args"] = (url, timeout)
        return io.BytesIO("department = \"Ä\"".encode())

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake_urlopen)
    assert sources.urllib_fetcher(RAW, 2.0) == 'department = "Ä"'
    assert seen["args"] == (RAW, 2.0)
