# Multi-repo architecture

This repo (agent-migration-toolkit) is the shared hub: schema, docs,
templates, and the Python tools. It gets published so department repos
can pip install it rather than vendoring code.

Each department (Engineering/Dev-Ops, Product/QA, Customer Support,
Sales/Account Mgmt, Legal/Compliance, Finance/Billing) owns its own
repo, containing only:

- process-table.toml, following schema/process-table.schema.toml
- a decision log (per templates/decision-log-entry.md)

Department repos are independent - a department team can edit and
merge its own process table without touching any other department's
repo or this hub.

## Cross-department aggregation

critical_path_timeline.py does not use git submodules. It fetches each
department repo's process-table.toml directly via
raw.githubusercontent.com (all department repos are public, matching
the existing convention already used across roebi's repos), then runs
gap_analysis_creator on each before building the combined critical
path / red-thread chart.
