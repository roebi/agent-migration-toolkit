# Requirements

Goal (Phase 0): a shared hub toolkit for the agent-migration program -
process-table schema, collection templates, gap analysis and a
cross-department critical path timeline - published so department repos
can pip install it.

Phase 0 input: `input/r-proc-requirements.md` (R-PROC-001..008),
`input/multi-repo-architecture.md`, `input/glossary.md`,
`input/red-line.md`, `input/Handover-State-legacy.md`, plus decisions
from 2026-11-08: timeline is in scope; durations come from new optional
schema fields; department repos are listed in a config file; timeline
output is TOML.

Primary users: department teams (fill in their process table, run the
gap analysis locally) and the program lead (runs the timeline across
all departments). Platform: Python CLI + library, installed via pip/uv.

## Requirement Groups

Build order derived from `depends-on`:

```
1. R-SCHEMA  - process-table data contract        depends-on: none
   R-SRC     - department source list + fetching  depends-on: none
2. R-GAP     - gap analysis                       depends-on: R-SCHEMA
   R-TPL     - collection templates               depends-on: R-SCHEMA
3. R-TIME    - critical path timeline             depends-on: R-SCHEMA, R-GAP, R-SRC
4. R-DEPLOY  - packaging, CI, publishing          depends-on: all
```

### R-SCHEMA-000 - Process-table data contract
depends-on: none

R-SCHEMA-001: Accept a process table as a TOML document with one
  `[[sub_process]]` entry per sub-process and reject a document without
  that array.
  driver: usability (departments edit one plain-text file per repo;
  covers R-PROC-005)
R-SCHEMA-002: Require the fields department, process, sub_process,
  automation_grade, output_artifact and interface_type on every entry and
  report each missing field by name.
  driver: usability (incomplete rows from collection meetings must be
  caught before analysis)
R-SCHEMA-003: Accept only `full`, `partial`, `manual` as automation_grade
  and report any other value with the offending row.
  driver: usability (covers R-PROC-003)
R-SCHEMA-004: Accept only `openapi`, `file`, `manual`, `none` as
  interface_type and report any other value with the offending row.
  driver: usability (covers R-PROC-004/007)
R-SCHEMA-005: Accept the optional fields input_artifact and notes as
  free text.
  driver: usability (covers R-PROC-006)
R-SCHEMA-006: Accept an optional non-negative number `effort_days` per
  entry and reject negative or non-numeric values.
  driver: usability (timeline needs durations; schema had none)
R-SCHEMA-007: Accept an optional list `depends_on` of sub_process names
  from the same department and reject names that do not exist in that
  department's table.
  driver: usability (turns a sub-process list into a process chain,
  R-PROC-007; red threads are per department, see glossary)
R-SCHEMA-008: Reject a table in which two entries share the same
  department and sub_process name.
  driver: usability (depends_on references must be unambiguous)
R-SCHEMA-009: Ship a documented example schema file that lists every
  field, its type and allowed values, and that itself passes validation.
  driver: usability (departments copy it as the start of their table)

### R-SRC-000 - Department source list and fetching
depends-on: none

R-SRC-001: Read a TOML source list with one entry per department, each
  holding a department name and exactly one of `url` or `path`.
  driver: usability (repo naming is not decided; a list works before it is)
R-SRC-002: Reject a source list entry that has both, or neither, of
  `url` and `path`, naming the entry.
  driver: usability (prevents silent misconfiguration)
R-SRC-003: Fetch a `url` entry only over HTTPS from host
  raw.githubusercontent.com and reject any other scheme or host.
  driver: usability (department repos are public; restricting the host
  keeps the tool from fetching arbitrary URLs from a config file)
R-SRC-004: Read a `path` entry from the local file system.
  driver: usability (offline use and testing without network)
R-SRC-005: Abort a single fetch that takes longer than a configurable
  timeout (default 10 s) and report it as a failure of that department.
  driver: usability (one unreachable repo must not hang the run)
R-SRC-006: Continue with the remaining departments when one source
  fails, and list every failed department with its reason in the result.
  driver: usability (program lead still gets a partial picture)
R-SRC-007: Reject fetched content whose `department` fields do not match
  the department named in the source list entry.
  driver: usability (catches a URL pointing at the wrong repo)

### R-GAP-000 - Gap analysis
depends-on: R-SCHEMA

R-GAP-001: Return one gap row per sub-process whose interface_type is
  not `openapi`, and none for `openapi` sub-processes.
  driver: usability (covers R-PROC-004)
R-GAP-002: Include department, process, sub_process, current_interface
  and a gap description in every gap row.
  driver: usability (row must be actionable without the source table)
R-GAP-003: Describe the gap per interface_type: `none` needs an artifact
  definition, `manual` needs a schema and an OpenAPI endpoint, `file`
  needs an OpenAPI wrap or bridge.
  driver: usability (tells the department the next step)
R-GAP-004: Provide a CLI command `gap-analysis-creator <table>` that
  writes the gap table as TOML to stdout, or to a file given with
  `-o/--output`.
  driver: usability (departments run it locally on their own table)
R-GAP-005: Exit with code 0 on success, and with code 1 plus a one-line
  error message on stderr (no stack trace) when the input file is
  missing, is not valid TOML or fails schema validation.
  driver: usability (today invalid input ends in a raw traceback)

### R-TPL-000 - Collection templates
depends-on: R-SCHEMA

R-TPL-001: Ship templates for meeting agenda, process collection form,
  process split worksheet, automation-grade decision tree and decision
  log entry.
  driver: usability (covers R-PROC-001/002; same meeting format in all
  six departments)
R-TPL-002: Ask in the process split worksheet for every required schema
  field and for effort_days and depends_on.
  driver: usability (meeting output maps 1:1 to the process table)
R-TPL-003: Contain no references to files that do not exist in the
  repository.
  driver: usability (decision tree currently links to a moved doc)

### R-TIME-000 - Critical path timeline
depends-on: R-SCHEMA, R-GAP, R-SRC

R-TIME-001: Load every department from the source list, validate each
  table against R-SCHEMA and compute its gap rows via R-GAP.
  driver: usability (one command for the program lead instead of six
  manual runs)
R-TIME-002: Schedule only gap rows; a gap row's depends_on predecessors
  that are not gaps count as already done.
  driver: usability (the timeline is the work to close gaps)
R-TIME-003: List gap rows without effort_days as `unestimated` and leave
  them out of the schedule.
  driver: usability (missing estimates are visible, not silently zero)
R-TIME-004: Compute per scheduled gap row its earliest start, earliest
  finish and slack in days, starting each department at day 0.
  driver: usability (shows what can start now and what can slip)
R-TIME-005: Mark the rows with zero slack as the department's critical
  path (red thread) and report its total length in days.
  driver: usability (glossary: red thread per department)
R-TIME-006: Assign each scheduled row to block `quick_ramp` if its
  earliest start is within the first 20% of the department's critical
  path length, otherwise to `hardening`.
  driver: usability (glossary: quick ramp ~20% / hardening ~80%)
R-TIME-007: Report the program length as the longest department
  critical path and name that department.
  driver: usability (program lead needs one end date)
R-TIME-008: Reject a department whose depends_on references form a cycle
  and name the sub-processes in the cycle.
  driver: usability (a cycle has no valid schedule)
R-TIME-009: Provide a CLI command `critical-path-timeline <sources>` that
  writes the timeline as TOML to stdout or to a file given with
  `-o/--output`.
  driver: usability (same usage pattern as gap-analysis-creator)
R-TIME-010: Exit with code 0 when all departments were processed, 2 when
  some departments failed (result still written), and 1 when the source
  list itself is invalid or no department could be processed.
  driver: usability (scripts and CI can tell partial from total failure)

### R-DEPLOY-000 - Packaging, CI and publishing
depends-on: R-SCHEMA, R-SRC, R-GAP, R-TPL, R-TIME

R-DEPLOY-001: Build the project as an installable Python package named
  `agent-migration-toolkit` that provides both CLI commands.
  driver: usability (department repos pip install instead of vendoring)
R-DEPLOY-002: Run tests with coverage, ruff lint and a security scan
  (bandit and semgrep) on every push and pull request, failing the run
  on any test failure, coverage below 80%, lint error or high-severity
  finding.
  driver: usability (legacy handover: SEC gates not wired in)
R-DEPLOY-003: Publish the package to PyPI from a version tag via Trusted
  Publishing, without stored API tokens.
  driver: usability (departments cannot install it today)
R-DEPLOY-004: Build a container image that runs the test suite by
  default and either CLI when given its name.
  driver: usability (reproducible run without a local Python setup)

## Non-Functional Requirements

NFR-01: Testability - pytest, line coverage >= 80% over `src/`, network
  calls replaceable in tests (no real HTTP in the test suite).
NFR-02: Portability - Python >= 3.11 on Linux, macOS and Windows; no
  OS-specific paths.
NFR-03: Reliability - every user error ends with a defined exit code and
  a one-line message; no stack traces for invalid input.
NFR-04: Security - read-only toward department repos (no writes, no
  credentials needed or stored); only HTTPS to raw.githubusercontent.com.
NFR-05: Red Line - the toolkit never changes customer- or license-relevant
  state; it only reads process tables and writes local output files.
NFR-06: Performance - a timeline over 6 departments with 200 sub-processes
  each completes in under 5 s excluding network time.
NFR-07: Dependencies - runtime dependencies limited to the standard
  library plus tomli-w.
NFR-08: Code style - ruff check passes with the project configuration.

## Out of Scope

- Creating or scaffolding the six department repos (deferred until the
  naming convention is decided).
- Graphical charts (Mermaid, PNG, HTML); output is TOML only.
- Cross-department dependencies in depends_on (red threads are
  independent per department).
- Writing to department repos, opening PRs or any automated change of
  their process tables.
- Resource levelling or calendar dates; the timeline is in working days
  from day 0.
- Implementing R-CTRL approval workflows (separate program track).

## Requirements Review

- [x] Dependency order respected (no group approved before its dependencies)
- [x] Every requirement has a driver
- [x] No conflicting requirements across groups
- [x] No gaps against the Phase 0 goal statement (R-PROC-001..007 mapped;
      R-PROC-008 iteration loop is the framework process itself)
- [x] Parity-driven requirements have an explicit usage/adoption hypothesis
      (none present)
- [x] Compliance-driven requirements reference the law/regulation and
      deadline (none present; Red Line is internal governance, NFR-05)
- [ ] Reviewed by: Claude agent on 2026-11-08 - awaiting approval by roebi
