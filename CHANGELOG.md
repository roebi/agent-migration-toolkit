# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- README shows `uv tool install agent-migration-toolkit` for installing
  both commands outside a project.

## [0.1.1] - 2026-11-08

The installed package behaves exactly as in 0.1.0; this release changes
only how releases are checked before they reach PyPI.

### Changed

- The release workflow runs the full CI gate set (tests with coverage on
  Linux, macOS and Windows, ruff, bandit and semgrep) on the released
  commit and publishes nothing to PyPI if any gate fails. Before, it
  re-ran only the tests.
- The check that the release tag equals `v` + the package version runs
  as its own job and stops the release early on a mismatch.

## [0.1.0] - 2026-11-08

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

[unreleased]: https://github.com/roebi/agent-migration-toolkit/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/roebi/agent-migration-toolkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/roebi/agent-migration-toolkit/releases/tag/v0.1.0
