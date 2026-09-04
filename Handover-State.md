# Handover State

## Project
agentifizierung-toolkit - shared hub repo for the agent-migration program
(process analysis, gap analysis, critical path timeline).

## Status
Hub repo scaffolded: schema, docs, templates, gap_analysis_creator tool
with passing tests, Podman scaffold. Department repos (Engineering/Dev-Ops,
Product/QA, Customer Support, Sales/Account Mgmt, Legal/Compliance,
Finance/Billing) do NOT exist yet - they get created per-department by
each team, consuming this hub via pip install once published, and holding
only their own process-table.yaml plus a decision log.

## Known issues
- gap_analysis_creator.py is not yet published to PyPI, so department
  repos cannot pip install it yet - only local/relative use for now.
- critical_path_timeline.py (multi-department aggregator over
  raw.githubusercontent.com) is not yet implemented - next step.
- No CI workflow file yet (SEC gates: semgrep/bandit not wired in).

## Deferred items
- Department repo scaffolding (6x), once naming is confirmed with Roebi.
- PyPI publish of the toolkit package.

## Next steps
- Define requirements for critical_path_timeline.py (R-PROC-005/007
  aggregation across department repos via raw.githubusercontent.com)
- Add CI workflow: semgrep/bandit on tools/, pytest gate
- Publish package to PyPI so department repos can pip install it
- Confirm department repo naming convention, scaffold first one
