import re
from pathlib import Path

import pytest

from agent_migration_toolkit.schema import REQUIRED_FIELDS, load_table

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SCHEMA_FILE = ROOT / "schema" / "process-table.schema.toml"
OPTIONAL_FIELDS = ("input_artifact", "notes", "effort_days", "depends_on")
PLANNING_FIELDS = ("effort_days", "depends_on")


def test_schema_example_passes_validation():
    rows = load_table(SCHEMA_FILE.read_text(encoding="utf-8"))
    assert rows


@pytest.mark.parametrize("field", REQUIRED_FIELDS + OPTIONAL_FIELDS)
def test_schema_example_documents_every_field(field):
    assert field in SCHEMA_FILE.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "name",
    [
        "meeting-agenda.md",
        "process-collection-form.md",
        "process-split-worksheet.md",
        "automation-grade-decision-tree.md",
        "decision-log-entry.md",
    ],
)
def test_template_exists(name):
    assert (TEMPLATES / name).is_file()


@pytest.mark.parametrize("field", REQUIRED_FIELDS + PLANNING_FIELDS)
def test_split_worksheet_asks_for_field(field):
    text = (TEMPLATES / "process-split-worksheet.md").read_text(encoding="utf-8")
    assert f"`{field}`" in text


FILE_REF = re.compile(r"[\w./-]+\.(?:md|toml)\b")


@pytest.mark.parametrize("template", sorted(TEMPLATES.glob("*.md")), ids=lambda p: p.name)
def test_template_references_only_existing_files(template):
    for ref in FILE_REF.findall(template.read_text(encoding="utf-8")):
        assert (TEMPLATES / ref).exists() or (ROOT / ref).exists(), ref
