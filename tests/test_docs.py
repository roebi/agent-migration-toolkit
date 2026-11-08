import re
import shlex
import shutil
from importlib.metadata import metadata
from pathlib import Path

import pytest

from agent_migration_toolkit.cli import gap_main, timeline_main
from agent_migration_toolkit.schema import REQUIRED_FIELDS, load_table

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


USAGE = ROOT / "docs" / "usage.md"
README = ROOT / "README.md"


@pytest.mark.parametrize(
    "needle",
    [
        *(f"`{field}`" for field in REQUIRED_FIELDS),
        "`input_artifact`", "`notes`", "`effort_days`", "`depends_on`",
        "`url`", "`path`", "relative", "absolute", "--timeout",
        "[[gap]]", "[program]", "[[department]]", "[[department.task]]",
        "[[department.unestimated]]", "[[failure]]",
        "| 0 |", "| 1 |", "| 2 |",
    ],
)
def test_usage_guide_documents(needle):
    assert needle in USAGE.read_text(encoding="utf-8")


CONSOLE_BLOCK = re.compile(r"```console\n(.*?)```", re.DOTALL)
COMMANDS = {"gap-analysis-creator": gap_main, "critical-path-timeline": timeline_main}
INSTALL_TOOLS = {"pip", "uv", "uvx"}


def _documented_commands(path):
    """Yield (command, expected exit code) for every `$ ...` line in console blocks."""
    if not path.exists():
        return
    for block in CONSOLE_BLOCK.findall(path.read_text(encoding="utf-8")):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            if not line.startswith("$ "):
                continue
            following = lines[index + 1] if index + 1 < len(lines) else ""
            match = re.fullmatch(r"# exit: (\d+)", following.strip())
            yield line[2:], int(match.group(1)) if match else 0


def _all_documented_commands():
    return [
        pytest.param(cmd, code, id=f"{doc.name}: {cmd}")
        for doc in (README, USAGE)
        for cmd, code in _documented_commands(doc)
    ]


def _no_network(url, timeout):
    raise AssertionError(f"documented examples must not need the network: {url}")


@pytest.mark.parametrize(("command", "expected"), _all_documented_commands())
def test_documented_command_runs_with_documented_exit_code(
    command, expected, tmp_path, monkeypatch
):
    argv = shlex.split(command)
    if argv[0] in INSTALL_TOOLS:
        pytest.skip("install command")
    assert argv[0] in COMMANDS, f"unknown command in docs: {argv[0]}"
    shutil.copytree(ROOT / "docs" / "examples", tmp_path / "docs" / "examples")
    monkeypatch.chdir(tmp_path)
    if argv[0] == "critical-path-timeline":
        code = timeline_main(argv[1:], fetcher=_no_network)
    else:
        code = gap_main(argv[1:])
    assert code == expected


def test_docs_contain_commands_for_both_tools():
    programs = {shlex.split(cmd)[0] for doc in (README, USAGE) for cmd, _ in _documented_commands(doc)}
    assert set(COMMANDS) <= programs


def test_every_example_process_table_is_valid():
    tables = sorted((ROOT / "docs" / "examples").glob("*process-table.toml"))
    assert tables
    for table in tables:
        load_table(table.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "needle",
    [
        "uv tool install agent-migration-toolkit",
        "pip install agent-migration-toolkit",
        "uv add agent-migration-toolkit",
        "gap-analysis-creator",
        "critical-path-timeline",
        "docs/usage.md",
        "CHANGELOG.md",
    ],
)
def test_readme_covers_install_quickstart_and_links(needle):
    assert needle in README.read_text(encoding="utf-8")


def test_readme_is_the_pypi_description(meta):
    assert meta["Description-Content-Type"] == "text/markdown"
    assert meta.get_payload().strip() == README.read_text(encoding="utf-8").strip()


def test_readme_links_are_absolute_for_pypi():
    links = re.findall(r"\]\(([^)]+)\)", README.read_text(encoding="utf-8"))
    assert links
    assert all(link.startswith(("https://", "#")) for link in links), links
