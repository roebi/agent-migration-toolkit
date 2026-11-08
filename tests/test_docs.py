from importlib.metadata import metadata

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
