import pytest


def make_row(**overrides):
    row = {
        "department": "Finance/Billing",
        "process": "Invoice run",
        "sub_process": "Match usage to contract",
        "automation_grade": "manual",
        "output_artifact": "match report",
        "interface_type": "manual",
    }
    row.update(overrides)
    return row


@pytest.fixture
def row():
    return make_row
