# Architecture

Input: `requirements.md` (approved 2026-11-08), `input/multi-repo-architecture.md`.

## Summary

A small Python package `agent_migration_toolkit` in src layout with one
module per requirement group. The business logic (schema validation,
gap analysis, scheduling) is made of pure functions over plain
dicts/dataclasses with no I/O. All side effects - reading files, HTTP
fetches, writing output, exit codes - live at the edges: `sources.py`
(input, with an injected fetcher) and `cli.py` (thin argparse wrappers).
Runtime dependencies stay at stdlib + tomli-w (NFR-07), so the CLI uses
argparse instead of Typer and HTTP uses `urllib.request` behind an
injectable callable.

## Module Structure

```
agent-migration-toolkit/
├── pyproject.toml                    R-DEPLOY-001 (2 console scripts)
├── uv.lock
├── Dockerfile, .containerignore,
│   entrypoint.sh, podman_build.sh,
│   podman_run.sh                     R-DEPLOY-004
├── .github/workflows/
│   ├── ci.yml                        R-DEPLOY-002
│   └── release.yml                   R-DEPLOY-003
├── schema/
│   └── process-table.schema.toml     R-SCHEMA-009 (example, must validate)
├── templates/*.md                    R-TPL-001..003
├── src/agent_migration_toolkit/
│   ├── __init__.py                   __version__
│   ├── schema.py                     R-SCHEMA-001..008
│   ├── gap.py                        R-GAP-001..003
│   ├── sources.py                    R-SRC-001..007
│   ├── timeline.py                   R-TIME-001..008
│   └── cli.py                        R-GAP-004/005, R-TIME-009/010
└── tests/
    ├── conftest.py                   row builder fixture
    ├── test_schema.py
    ├── test_gap.py
    ├── test_sources.py
    ├── test_timeline.py              incl. NFR-06 performance test
    ├── test_cli.py
    ├── test_package.py               R-DEPLOY-001 (version, console scripts)
    └── test_templates.py             R-TPL-001..003, R-SCHEMA-009
```

The current `gap_analysis_creator.py` is split into `schema.py`
(validation, loading), `gap.py` (gap rows) and `cli.py` (`main`). Its
tests move into `test_schema.py` / `test_gap.py` / `test_cli.py`.

## Components

### schema
- Responsibility: parse and validate a process table (the data contract).
- Public interface:
  - `class ValidationError(ValueError)` - message lists every problem found.
  - `parse_table(text: str) -> list[dict]` - TOML text to rows; raises
    `ValidationError` if not TOML or no `[[sub_process]]` array (001).
  - `validate_table(rows) -> list[str]` - all problems as strings with
    the offending row: missing fields (002), bad enums (003/004), bad
    `effort_days` (006), unknown `depends_on` names within the same
    department (007), duplicate department+sub_process (008). Optional
    free-text fields are accepted unchecked (005).
  - `load_table(text: str) -> list[dict]` - `parse_table` + raise
    `ValidationError` if `validate_table` returns anything.
  - Constants `REQUIRED_FIELDS`, `VALID_GRADES`, `VALID_INTERFACE_TYPES`.
- Dependencies: stdlib `tomllib`.

### gap
- Responsibility: derive gap rows from a validated table.
- Public interface: `compute_gaps(rows) -> list[dict]` (001/002) with
  `gap_description(interface_type) -> str` (003). Gap rows also carry
  `effort_days` and `depends_on` through when present, for the timeline.
- Dependencies: none (expects rows already validated by `schema`).

### sources
- Responsibility: read the department source list and fetch each table.
- Public interface:
  - `@dataclass Source(department, url | None, path | None)`
  - `parse_sources(text: str) -> list[Source]` (001/002), URL rule
    checked here: scheme `https`, host `raw.githubusercontent.com` (003).
  - `Fetcher = Callable[[str, float], str]` - url, timeout -> body.
  - `urllib_fetcher(url, timeout) -> str` - the only real network code.
  - `@dataclass Loaded(department, rows | None, error | None)`
  - `load_all(sources, fetcher, timeout=10.0, base_dir: Path) -> list[Loaded]`
    reads `path` (004, relative to the source list's directory) or calls
    `fetcher` (005), validates via `schema.load_table`, checks the
    `department` field matches (007), and turns every exception of one
    source into `Loaded(error=...)` so the others continue (006).
- Dependencies: `schema`; stdlib `urllib.request`, `urllib.parse`.

### timeline
- Responsibility: critical path scheduling per department and overall.
- Public interface:
  - `find_cycle(rows) -> list[str] | None` (008) - over the department's
    full `depends_on` graph.
  - `schedule_department(department, rows) -> dict` - computes gaps via
    `gap.compute_gaps`; splits them into `unestimated` (003) and
    scheduled tasks; forward/backward pass (004); critical path (005);
    blocks (006). Raises `ValidationError` on a cycle.
  - `build_timeline(loaded: list[Loaded]) -> dict` - schedules every
    department, turns per-department errors into `failure` entries,
    and adds the `program` summary (007).
- Scheduling rules (pure, from R-TIME):
  - Tasks = gap rows with `effort_days`. Predecessors that are not
    tasks (openapi rows = done, R-TIME-002; unestimated rows) are
    ignored for scheduling. A task with unestimated gap predecessors
    lists them in `waits_on_unestimated` (OQ-1, decided option a).
  - Forward pass: `ES = max(EF of task predecessors, default 0)`,
    `EF = ES + effort_days`. Department length `L = max(EF, default 0)`.
  - Backward pass: `LF = min(LS of task successors, default L)`,
    `LS = LF - effort_days`, `slack = LS - ES`.
  - `critical = abs(slack) < 1e-9`; red thread = critical tasks ordered by ES.
  - `block = "quick_ramp" if L == 0 or ES < 0.2 * L else "hardening"`.
  - Program length = max department `L`; ties pick the first in source order.
- Dependencies: `schema` (error type), `gap`.

### cli
- Responsibility: argument parsing, file I/O for output, exit codes.
- Public interface:
  - `gap_main(argv=None) -> int` -> console script `gap-analysis-creator`.
  - `timeline_main(argv=None, fetcher=urllib_fetcher) -> int` -> console
    script `critical-path-timeline`; `--timeout` option (default 10).
  - Both write TOML via `tomli_w` to stdout or `-o/--output`.
  - Exit codes: gap 0/1 (R-GAP-005); timeline 0 all ok, 2 some failed
    (output still written), 1 invalid source list or nothing loaded
    (R-TIME-010). Errors: one line `error: <message>` on stderr, no
    traceback (NFR-03) - `ValidationError`, `OSError`, `TOMLDecodeError`
    are caught at this layer only.
- Dependencies: `schema`, `gap`, `sources`, `timeline`, `tomli_w`.

## Data Flow

Gap analysis:

```
table.toml --read--> cli.gap_main --text--> schema.load_table --rows-->
gap.compute_gaps --gaps--> tomli_w.dumps({"gap": gaps}) --> stdout | file
```

Timeline:

```
sources.toml --read--> sources.parse_sources --[Source]-->
sources.load_all(fetcher) --per source: path read | fetcher(url)
                            -> schema.load_table -> department check-->
[Loaded(rows | error)] --> timeline.build_timeline
    per ok department: find_cycle -> gap.compute_gaps -> CPM passes
    per error: failure entry
--> dict --> tomli_w --> stdout | file;   exit code from failures
```

Timeline output (TOML):

```toml
[program]
length_days = 42.0
critical_department = "Finance/Billing"

[[department]]
name = "Finance/Billing"
critical_path_days = 42.0
critical_path = ["Match usage to contract", "..."]

[[department.task]]
process = "Invoice run"
sub_process = "Match usage to contract"
current_interface = "manual"
effort_days = 10.0
earliest_start = 0.0
earliest_finish = 10.0
slack_days = 0.0
critical = true
block = "quick_ramp"
waits_on_unestimated = []

[[department.unestimated]]
process = "..."
sub_process = "..."
current_interface = "file"

[[failure]]
department = "Legal/Compliance"
reason = "timeout after 10.0 s"
```

## Technology Choices

| Decision | Choice | Rationale |
|---|---|---|
| Language/runtime | Python >= 3.11 | `tomllib` in stdlib; NFR-02 |
| CLI | argparse (not Typer) | NFR-07 limits runtime deps to stdlib + tomli-w |
| TOML read / write | `tomllib` / `tomli-w` | existing choice, NFR-07 |
| HTTP | `urllib.request` behind `Fetcher` callable | no extra dependency; fake in tests (no `responses` lib needed) |
| Data shapes | dicts for table rows, small dataclasses for `Source`/`Loaded` | rows map 1:1 to TOML, no conversion layer (KISS) |
| Packaging | uv, `uv_build`, src layout | already in place |
| Tests | pytest + pytest-cov, >= 80% over `src/` | NFR-01 |
| Lint | ruff (project config) | NFR-08 |
| Security scan | bandit + semgrep in CI | R-DEPLOY-002 |
| CI | GitHub Actions, matrix Python 3.11 + 3.13 on ubuntu, macos, windows | NFR-02, framework default 3.13 |
| Publish | PyPI Trusted Publishing (OIDC) on tag `v*.*.*` | R-DEPLOY-003; name `agent-migration-toolkit` is free on PyPI (checked 2026-11-08) |
| Container | python:3.12-slim + uv | R-DEPLOY-004, already scaffolded |

## Testability Constraints

- Pure core - `schema`, `gap`, `timeline` take and return plain data; no
  file, network or clock access. Tested with in-memory rows.
- Text in, not paths - `schema.parse_table`/`load_table` and
  `sources.parse_sources` take strings, so tests need no files.
- File I/O - only `sources.load_all` (path entries, via `base_dir: Path`)
  and `cli` touch the file system; tests use pytest `tmp_path`.
- Network - `sources.load_all` and `cli.timeline_main` receive a
  `fetcher` callable; tests pass a fake that returns text or raises
  (`TimeoutError`, `URLError`). `urllib_fetcher` itself is a 3-line
  wrapper, tested with `monkeypatch` on `urllib.request.urlopen`.
  No real HTTP in the suite (NFR-01).
- CLI - `gap_main`/`timeline_main` take `argv` and return the exit code;
  tests use `capsys` for stdout/stderr, no subprocess.
- No global state - timeout, fetcher and base_dir are passed explicitly.
- Schema example and templates - `test_templates.py` validates
  `schema/process-table.schema.toml` with `load_table` (R-SCHEMA-009),
  checks the split worksheet mentions every schema field (R-TPL-002)
  and that every relative file path mentioned in `templates/` exists
  (R-TPL-003).

Implementation notes (TDD phase, 2026-11-08): fakes are defined inline
in the tests, so no `fixtures/` directory was needed. `schema.parse_toml`
is shared by `parse_table` and `sources.parse_sources`. Topological order
and cycle detection use stdlib `graphlib`. Near-zero slack (< 1e-9) is
reported as 0. The timeline CLI prints one `warning:` line per failed
department on stderr when it exits with 2.

## Requirement Traceability

| Group | Module | Test file |
|---|---|---|
| R-SCHEMA-001..008 | schema.py | test_schema.py |
| R-SCHEMA-009 | schema/process-table.schema.toml | test_templates.py |
| R-SRC-001..007 | sources.py | test_sources.py |
| R-GAP-001..003 | gap.py | test_gap.py |
| R-GAP-004/005 | cli.py | test_cli.py |
| R-TPL-001..003 | templates/ | test_templates.py |
| R-TIME-001..008 | timeline.py (+ sources.py for 001) | test_timeline.py |
| R-TIME-009/010 | cli.py | test_cli.py |
| R-DEPLOY-001 | pyproject.toml | test_package.py, `uv build` |
| R-DEPLOY-002..004 | workflows, Dockerfile | CI run, container build (not yet run, OQ-2) |
| NFR-06 | timeline.py | test_timeline.py (6 x 200 rows < 5 s) |

## Open Questions

- OQ-1 (resolved 2026-11-08, option a): a task depending on an
  unestimated gap row is still scheduled; the edge is ignored and the
  task lists the predecessor in `waits_on_unestimated`. R-TIME-003
  unchanged.
- OQ-2: GitHub remote and PyPI Trusted Publisher are not set up yet (no
  remote configured, no `gh` in the dev container). Needed before
  R-DEPLOY-002/003 can be verified; implementation can proceed without.
