"""Structure tests for the GitHub workflows (R-DEPLOY-002, -005, -006)."""

from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def run_commands(job):
    return " ".join(step.get("run", "") for step in job.get("steps", []))


def all_run_commands(workflow):
    return " ".join(run_commands(job) for job in workflow["jobs"].values())


def test_ci_runs_tests_with_coverage_lint_and_security_scans():
    commands = all_run_commands(load("ci.yml"))
    for gate in ("pytest --cov", "ruff check", "bandit", "semgrep"):
        assert gate in commands
