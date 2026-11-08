import pytest

from agent_migration_toolkit.schema import ValidationError
from agent_migration_toolkit.sources import Source, parse_sources

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
