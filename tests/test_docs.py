import re
from importlib.metadata import metadata
from pathlib import Path

import pytest

REPO = "https://github.com/roebi/agent-migration-toolkit"


@pytest.fixture(scope="module")
def meta():
    return metadata("agent-migration-toolkit")


def test_metadata_declares_project_urls(meta):
    urls = dict(entry.split(", ", 1) for entry in meta.get_all("Project-URL"))
    assert urls == {
        "Homepage": REPO,
        "Repository": REPO,
        "Changelog": f"{REPO}/blob/main/CHANGELOG.md",
        "Issues": f"{REPO}/issues",
    }


def test_metadata_declares_license_python_classifiers_and_keywords(meta):
    assert meta["License-Expression"] == "MIT"
    classifiers = meta.get_all("Classifier")
    for version in ("3.11", "3.12", "3.13"):
        assert f"Programming Language :: Python :: {version}" in classifiers
    assert "agent-migration" in meta["Keywords"]


ROOT = Path(__file__).resolve().parents[1]
VERSION_HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
CHANGE_TYPES = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}


def _changelog():
    return (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_changelog_follows_keep_a_changelog_1_1_0():
    text = _changelog()
    assert text.startswith("# Changelog\n")
    assert "https://keepachangelog.com/en/1.1.0/" in text
    assert "https://semver.org/spec/v2.0.0.html" in text
    assert "\n## [Unreleased]\n" in text


def test_changelog_uses_only_standard_change_types():
    types = set(re.findall(r"^### (.+)$", _changelog(), re.MULTILINE))
    assert types and types <= CHANGE_TYPES


def test_changelog_has_link_reference_for_every_section():
    text = _changelog()
    assert re.search(r"^\[unreleased\]: https://github.com/roebi/agent-migration-toolkit/", text,
                     re.MULTILINE | re.IGNORECASE)
    for version in VERSION_HEADING.findall(text):
        assert re.search(rf"^\[{re.escape(version)}\]: https://", text, re.MULTILINE), version
