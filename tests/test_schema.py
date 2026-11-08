import pytest

from agent_migration_toolkit.schema import ValidationError, parse_table


def test_parse_table_returns_rows_from_sub_process_array():
    text = '[[sub_process]]\ndepartment = "A"\n\n[[sub_process]]\ndepartment = "B"\n'
    assert parse_table(text) == [{"department": "A"}, {"department": "B"}]


def test_parse_table_without_sub_process_array_raises():
    with pytest.raises(ValidationError, match=r"\[\[sub_process\]\]"):
        parse_table('title = "x"\n')


def test_parse_table_with_invalid_toml_raises():
    with pytest.raises(ValidationError, match="not valid TOML"):
        parse_table("[[sub_process]\n")
