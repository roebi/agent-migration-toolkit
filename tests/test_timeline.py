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


def test_gap_without_effort_is_unestimated_and_not_scheduled(row):
    rows = [row(sub_process="Known", effort_days=1), row(sub_process="Unknown")]
    result = schedule_department("Finance/Billing", rows)
    assert _names(result["task"]) == ["Known"]
    assert _names(result["unestimated"]) == ["Unknown"]
    assert result["unestimated"][0]["current_interface"] == "manual"
