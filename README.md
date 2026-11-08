# agent-migration-toolkit

Shared hub toolkit for the agent-migration program. Departments describe
their processes in a TOML process table; the toolkit shows which
handoffs are not yet clean OpenAPI contracts (gaps) and builds a
critical path timeline across all departments.

- **`gap-analysis-creator`** - one department: process table -> gap table,
  with the next step for each gap.
- **`critical-path-timeline`** - all departments: reads each department's
  process table (local file or `raw.githubusercontent.com`) and writes
  the critical path (red thread) per department, the quick ramp /
  hardening split and the program length.
- **Schema and templates** - the process-table contract and the
  collection meeting templates used in every department.

The toolkit only reads process tables and writes local TOML files; it
never changes anything in a department repo.

## Installation

Python 3.11 or newer.

```console
$ pip install agent-migration-toolkit
```

or in a uv project:

```console
$ uv add agent-migration-toolkit
```

or as standalone commands, available outside any project:

```console
$ uv tool install agent-migration-toolkit
```

## Quickstart

The example files are in
[`docs/examples/`](https://github.com/roebi/agent-migration-toolkit/tree/main/docs/examples).

Gap table for one department:

```console
$ gap-analysis-creator docs/examples/finance-process-table.toml
```

Timeline across departments, listed in a source list:

```console
$ critical-path-timeline docs/examples/sources.toml -o timeline.toml
```

A source list names each department and where its table lives:

```toml
[[department]]
name = "Finance/Billing"
path = "finance-process-table.toml"

[[department]]
name = "Legal/Compliance"
url = "https://raw.githubusercontent.com/<owner>/<repo>/main/process-table.toml"
```

Exit codes: 0 success, 1 invalid input, 2 timeline written but some
departments failed.

## Documentation

- [Usage guide](https://github.com/roebi/agent-migration-toolkit/blob/main/docs/usage.md) -
  process-table fields, source list, output format, exit codes
- [Process-table schema](https://github.com/roebi/agent-migration-toolkit/blob/main/schema/process-table.schema.toml) -
  copy it as the start of a department's `process-table.toml`
- [Collection templates](https://github.com/roebi/agent-migration-toolkit/tree/main/templates)
- [CHANGELOG.md](https://github.com/roebi/agent-migration-toolkit/blob/main/CHANGELOG.md)

## Development

```console
$ uv sync
$ uv run pytest --cov=src --cov-report=term-missing
$ uv run ruff check src/ tests/
```

## License

[MIT](https://github.com/roebi/agent-migration-toolkit/blob/main/LICENSE)
