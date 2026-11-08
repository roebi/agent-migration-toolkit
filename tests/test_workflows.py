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


def triggers(workflow):
    # PyYAML (YAML 1.1) reads the bare key `on` as boolean True.
    return workflow.get("on", workflow.get(True))


def test_ci_can_be_called_as_reusable_workflow():
    assert "workflow_call" in triggers(load("ci.yml"))


def needs(job):
    value = job.get("needs", [])
    return [value] if isinstance(value, str) else value


def upstream(jobs, name):
    """All jobs that must finish before job `name` starts."""
    found = set()
    for dep in needs(jobs[name]):
        found |= {dep} | upstream(jobs, dep)
    return found


def test_release_publishes_only_after_ci_gates():
    jobs = load("release.yml")["jobs"]
    assert jobs["gates"]["uses"] == "./.github/workflows/ci.yml"
    assert "gates" in upstream(jobs, "publish")


def test_release_publishes_only_when_tag_matches_package_version():
    jobs = load("release.yml")["jobs"]
    check = run_commands(jobs["check-tag"])
    assert "uv version --short" in check
    assert '"v${version}" = "${GITHUB_REF_NAME}"' in check
    assert "check-tag" in upstream(jobs, "publish")


def test_release_grants_oidc_token_only_to_publish():
    workflow = load("release.yml")
    assert workflow["permissions"] == {"contents": "read"}
    for name, job in workflow["jobs"].items():
        has_token = job.get("permissions", {}).get("id-token") == "write"
        assert has_token == (name == "publish")
