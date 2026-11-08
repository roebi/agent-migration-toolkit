# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `gap-analysis-creator` command: reads a department process table and
  writes one gap row per sub-process whose interface is not yet an
  OpenAPI contract, with the next step per interface type.
- `critical-path-timeline` command: reads a source list of department
  process tables (local paths or `https://raw.githubusercontent.com`
  URLs) and writes the critical path (red thread) per department, the
  quick ramp / hardening split and the program length.
- Process-table schema with the optional fields `effort_days` and
  `depends_on`; every validation problem is reported at once.
- Exit codes: 0 success, 1 invalid input, 2 timeline written but some
  departments failed. Errors are one line on stderr, never a traceback.
- Collection meeting templates: agenda, process collection form, process
  split worksheet, automation-grade decision tree, decision log entry.
- README, usage guide with runnable examples, and this changelog.
- CI on Python 3.11 and 3.13 (Linux, macOS, Windows) with coverage,
  ruff, bandit and semgrep gates; release to PyPI via Trusted Publishing.

### Security

- URL sources are fetched only over HTTPS from
  `raw.githubusercontent.com`, including redirects.

[unreleased]: https://github.com/roebi/agent-migration-toolkit/commits/main
