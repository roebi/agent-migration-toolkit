from importlib.metadata import entry_points, version

import agent_migration_toolkit


def test_version_matches_distribution_metadata():
    assert agent_migration_toolkit.__version__ == version("agent-migration-toolkit")


def test_both_console_scripts_are_installed():
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts["gap-analysis-creator"] == "agent_migration_toolkit.cli:gap_main"
    assert scripts["critical-path-timeline"] == "agent_migration_toolkit.cli:timeline_main"
