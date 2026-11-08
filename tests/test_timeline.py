from agent_migration_toolkit.timeline import schedule_department


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
