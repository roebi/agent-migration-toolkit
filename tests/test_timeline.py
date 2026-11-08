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


def _by_name(result):
    return {task["sub_process"]: task for task in result["task"]}


def test_forward_and_backward_pass_compute_start_finish_and_slack(row):
    # A(3) -> C(2); B(1) -> C ; D(1) independent
    rows = [
        row(sub_process="A", effort_days=3),
        row(sub_process="B", effort_days=1),
        row(sub_process="C", effort_days=2, depends_on=["A", "B"]),
        row(sub_process="D", effort_days=1),
    ]
    tasks = _by_name(schedule_department("Finance/Billing", rows))
    assert (tasks["A"]["earliest_start"], tasks["A"]["earliest_finish"]) == (0, 3)
    assert (tasks["C"]["earliest_start"], tasks["C"]["earliest_finish"]) == (3, 5)
    assert tasks["A"]["slack_days"] == 0
    assert tasks["B"]["slack_days"] == 2
    assert tasks["C"]["slack_days"] == 0
    assert tasks["D"]["slack_days"] == 4


def test_task_output_has_process_interface_and_effort(row):
    [task] = schedule_department("Finance/Billing", [row(effort_days=2.5)])["task"]
    assert task["process"] == "Invoice run"
    assert task["current_interface"] == "manual"
    assert task["effort_days"] == 2.5


def test_tasks_are_scheduled_regardless_of_row_order(row):
    rows = [
        row(sub_process="Late", effort_days=1, depends_on=["Early"]),
        row(sub_process="Early", effort_days=2),
    ]
    tasks = _by_name(schedule_department("Finance/Billing", rows))
    assert tasks["Late"]["earliest_start"] == 2
