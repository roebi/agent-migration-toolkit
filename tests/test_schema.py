import pytest

from agent_migration_toolkit.schema import (
    ValidationError,
    load_table,
    parse_table,
    validate_table,
)


def test_parse_table_returns_rows_from_sub_process_array():
    text = '[[sub_process]]\ndepartment = "A"\n\n[[sub_process]]\ndepartment = "B"\n'
    assert parse_table(text) == [{"department": "A"}, {"department": "B"}]


def test_parse_table_without_sub_process_array_raises():
    with pytest.raises(ValidationError, match=r"\[\[sub_process\]\]"):
        parse_table('title = "x"\n')


def test_parse_table_with_invalid_toml_raises():
    with pytest.raises(ValidationError, match="not valid TOML"):
        parse_table("[[sub_process]\n")


def test_validate_table_valid_row_has_no_errors(row):
    assert validate_table([row()]) == []


def test_validate_table_reports_each_missing_field_by_name(row):
    bad = row()
    del bad["process"]
    del bad["output_artifact"]
    errors = validate_table([bad])
    assert len(errors) == 1
    assert "process" in errors[0] and "output_artifact" in errors[0]


def test_validate_table_reports_invalid_automation_grade_with_row(row):
    errors = validate_table([row(automation_grade="mostly")])
    assert len(errors) == 1
    assert "automation_grade" in errors[0] and "'mostly'" in errors[0]
    assert "Match usage to contract" in errors[0]


@pytest.mark.parametrize("grade", ["full", "partial", "manual"])
def test_validate_table_accepts_valid_automation_grades(row, grade):
    assert validate_table([row(automation_grade=grade)]) == []


def test_validate_table_reports_invalid_interface_type_with_row(row):
    errors = validate_table([row(interface_type="carrier_pigeon")])
    assert len(errors) == 1
    assert "interface_type" in errors[0] and "'carrier_pigeon'" in errors[0]


@pytest.mark.parametrize("itype", ["openapi", "file", "manual", "none"])
def test_validate_table_accepts_valid_interface_types(row, itype):
    assert validate_table([row(interface_type=itype)]) == []


def test_validate_table_accepts_optional_free_text_fields(row):
    assert validate_table([row(input_artifact="usage log", notes="sent by email")]) == []


@pytest.mark.parametrize("effort", [0, 3, 2.5])
def test_validate_table_accepts_non_negative_effort_days(row, effort):
    assert validate_table([row(effort_days=effort)]) == []


@pytest.mark.parametrize("effort", [-1, "five", True])
def test_validate_table_rejects_negative_or_non_numeric_effort_days(row, effort):
    errors = validate_table([row(effort_days=effort)])
    assert len(errors) == 1
    assert "effort_days" in errors[0]


def test_validate_table_accepts_depends_on_within_same_department(row):
    rows = [row(sub_process="A"), row(sub_process="B", depends_on=["A"])]
    assert validate_table(rows) == []


def test_validate_table_rejects_unknown_depends_on_name(row):
    errors = validate_table([row(sub_process="B", depends_on=["Ghost"])])
    assert len(errors) == 1
    assert "depends_on" in errors[0] and "'Ghost'" in errors[0]


def test_validate_table_rejects_depends_on_from_other_department(row):
    rows = [
        row(department="Legal/Compliance", sub_process="A"),
        row(department="Finance/Billing", sub_process="B", depends_on=["A"]),
    ]
    errors = validate_table(rows)
    assert len(errors) == 1
    assert "'A'" in errors[0]


def test_validate_table_rejects_depends_on_that_is_not_a_list_of_strings(row):
    errors = validate_table([row(depends_on="A")])
    assert len(errors) == 1
    assert "depends_on" in errors[0]


def test_validate_table_rejects_duplicate_sub_process_in_same_department(row):
    errors = validate_table([row(), row()])
    assert len(errors) == 1
    assert "duplicate" in errors[0]


def test_validate_table_allows_same_sub_process_name_in_other_department(row):
    rows = [row(), row(department="Legal/Compliance")]
    assert validate_table(rows) == []


def test_load_table_returns_valid_rows():
    text = (
        '[[sub_process]]\ndepartment = "D"\nprocess = "P"\nsub_process = "S"\n'
        'automation_grade = "full"\noutput_artifact = "o"\ninterface_type = "openapi"\n'
    )
    assert load_table(text)[0]["sub_process"] == "S"


def test_load_table_raises_with_all_problems():
    text = '[[sub_process]]\ndepartment = "D"\n\n[[sub_process]]\ndepartment = "E"\n'
    with pytest.raises(ValidationError) as excinfo:
        load_table(text)
    assert str(excinfo.value).count("missing fields") == 2


def test_parse_table_with_non_table_entries_raises():
    with pytest.raises(ValidationError, match=r"\[\[sub_process\]\]"):
        parse_table("sub_process = [1, 2]\n")


def test_validate_table_reports_non_string_required_field(row):
    errors = validate_table([row(department=["Finance"])])
    assert len(errors) == 1
    assert "department" in errors[0] and "string" in errors[0]


@pytest.mark.parametrize("effort", [float("inf"), float("nan")])
def test_validate_table_rejects_non_finite_effort_days(row, effort):
    assert len(validate_table([row(effort_days=effort)])) == 1


def test_validate_table_reports_missing_fields_and_other_problems_of_same_row(row):
    bad = row(interface_type="carrier_pigeon", effort_days=-1)
    del bad["automation_grade"]
    errors = validate_table([bad])
    assert len(errors) == 3
    assert any("missing fields ['automation_grade']" in e for e in errors)
    assert any("invalid interface_type 'carrier_pigeon'" in e for e in errors)
    assert any("effort_days" in e for e in errors)


def test_validate_table_does_not_report_enum_twice_for_non_string_value(row):
    errors = validate_table([row(interface_type=5)])
    assert len(errors) == 1
    assert "fields must be strings: ['interface_type']" in errors[0]
