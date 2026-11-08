# Handover-State.md

```yaml
skill: orchestrate-sw-dev-en
goal: >-
  Shared hub toolkit for the agent-migration program - process-table
  schema, templates, gap analysis and a cross-department critical path
  timeline - published so department repos can pip install it.
current_phase: release
results:
  - phase: requirements
    status: done
    output: requirements.md - 7 groups, 43 requirements, 8 NFRs; review passed, approved by roebi 2026-11-08 (R-DOC added from review F-04) (input: input/r-proc-requirements.md, input/glossary.md, input/red-line.md, input/Handover-State-legacy.md)
  - phase: design
    status: done
    output: architecture.md - 5 components; OQ-1 resolved (option a), OQ-2 open (GitHub remote/PyPI setup, blocks only R-DEPLOY-002/003 verification); approved by roebi 2026-11-08 (input: input/multi-repo-architecture.md)
  - phase: implement
    status: done
    output: all 43 requirements (incl. R-DOC added after review 1) + NFR-06 implemented test-first; 185 tests passed + 5 skipped (install commands in docs), 100% coverage, ruff/bandit/semgrep clean; CI + release workflows and container written but not yet run (OQ-2, review F-10)
  - phase: review
    status: done
    output: review-checklist.md - review 2 passed 2026-11-08 - 0 critical, 0 major; F-01..F-06, F-08, F-09, F-11, F-12 fixed; F-07 accepted; F-10 container verified by roebi, CI green on GitHub (run 42487302254)
  - phase: release
    status: done
    output: v0.1.0 released 2026-11-08 - GitHub release + tag v0.1.0 on 0627ae3 (created by roebi in the web GUI); release.yml run 42488225444 green; published to https://pypi.org/project/agent-migration-toolkit/0.1.0/ via trusted publishing; install from PyPI verified (both CLIs on docs/examples)
exit_condition_met: true
```

## Open items after v0.1.0

- Decide NFR-02 scope: keep native Windows/macOS in CI, or Linux only
  (Windows via WSL/podman) - requirement change, next iteration.
- Review F-07 (several asserts per test) accepted, no action.
- Deferred from the start: department repo scaffolding (6x) once the
  naming convention is decided; out of scope of the toolkit.
- Next iteration starts again at requirements (orchestrate-sw-dev-en),
  e.g. R-API if an HTTP/OpenAPI interface is wanted.

## Context

`input/` holds the pre-framework process files (legacy handover, early
requirements and architecture, glossary, red line). They are input for
the requirements and design phases, not living documents.

## TDD loop state (apply-tdd-loop-en)

```yaml
skill: apply-tdd-loop-en
entry_point: A (requirements.md) + B (existing gap_analysis_creator.py)
language: Python 3.11+
test_framework: pytest + pytest-cov
order: R-SCHEMA, R-SRC, R-GAP, R-TPL, R-TIME, CLI (R-GAP-004/005, R-TIME-009/010), R-DEPLOY
done: [R-SCHEMA-001..009, R-SRC-001..007, R-GAP-001..005, R-TPL-001..003, R-TIME-001..010, R-DOC-001..005, R-DEPLOY-001..004, NFR-06]
current: none
last_green_commit: 5eacdf6
exit_condition_met: true
```
