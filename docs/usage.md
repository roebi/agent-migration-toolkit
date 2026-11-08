# Usage guide

The toolkit has two commands:

- `gap-analysis-creator` - one department: process table -> gap table
- `critical-path-timeline` - all departments: source list -> timeline

Both read and write TOML. All examples below run from the repository
root on the files in [`docs/examples/`](examples/); the test suite runs
every command on this page and checks its exit code.

## 1. The process table

Each department keeps one `process-table.toml` with one `[[sub_process]]`
entry per sub-process. Start from
[`schema/process-table.schema.toml`](../schema/process-table.schema.toml)
and fill it from the collection meeting (see `templates/`).

| Field | Required | Type | Meaning |
|---|---|---|---|
| `department` | yes | string | department name, e.g. `Finance/Billing` |
| `process` | yes | string | parent process |
| `sub_process` | yes | string | the sub-process; unique within the department |
| `automation_grade` | yes | `full` / `partial` / `manual` | how much runs without a human today |
| `output_artifact` | yes | string | what the sub-process produces |
| `interface_type` | yes | `openapi` / `file` / `manual` / `none` | how the output reaches the next sub-process |
| `input_artifact` | no | string | what the sub-process consumes |
| `notes` | no | string | free text, e.g. "touches customer data" |
| `effort_days` | no | number >= 0 | working days to close the gap; needed for the timeline |
| `depends_on` | no | list of strings | `sub_process` names of the same department that must be done first |

`interface_type` decides whether a sub-process is a gap:

| `interface_type` | Gap? | Next step |
|---|---|---|
| `openapi` | no | already a clean machine contract |
| `file` | yes | needs an OpenAPI wrap or bridge |
| `manual` | yes | needs a schema and an OpenAPI endpoint |
| `none` | yes | needs an artifact definition first |

Validation reports every problem at once, with the row it belongs to,
also several problems of the same row: missing or non-string required
fields, unknown enum values, negative or
non-finite `effort_days`, `depends_on` names that do not exist in the same
department, and duplicate `sub_process` names.

## 2. Gap analysis

```console
$ gap-analysis-creator docs/examples/finance-process-table.toml
```

Writes one `[[gap]]` per sub-process whose `interface_type` is not
`openapi` to stdout:

```toml
[[gap]]
department = "Finance/Billing"
process = "Invoice run"
sub_process = "Collect usage log"
current_interface = "file"
gap = "file-based handoff - needs an OpenAPI wrap or bridge"
effort_days = 3
```

`effort_days` and `depends_on` are copied when present. Write to a file
instead of stdout with `-o`:

```console
$ gap-analysis-creator docs/examples/finance-process-table.toml -o gaps.toml
```

An invalid table ends with exit code 1 and one line on stderr:

```console
$ gap-analysis-creator docs/examples/broken-table.toml
# exit: 1
error: row 1 (Product/QA/Run regression suite): missing fields ['automation_grade', 'output_artifact']; row 1 (Product/QA/Run regression suite): invalid interface_type 'carrier_pigeon'
```

## 3. Critical path timeline

### The source list

The timeline reads a source list with one `[[department]]` entry per
department. Each entry has a `name` and exactly one of `url` or `path`:

```toml
[[department]]
name = "Finance/Billing"
path = "finance-process-table.toml"

[[department]]
name = "Legal/Compliance"
url = "https://raw.githubusercontent.com/<owner>/<repo>/main/process-table.toml"
```

- `url` - fetched over HTTPS from `raw.githubusercontent.com` only, also
  for redirects; any other scheme or host is rejected. Each fetch stops
  after `--timeout` seconds (default 10).
- `path` - a local file. A relative path is resolved against the
  directory of the source list, not the current directory. An absolute
  path is used as is, so a source list can point anywhere on your disk:
  only use source lists you trust.
- Every `department` field in a fetched table must equal the entry's
  `name`; this catches a URL that points at the wrong repo.

### Running it

```console
$ critical-path-timeline docs/examples/sources.toml
```

```console
$ critical-path-timeline docs/examples/sources.toml -o timeline.toml --timeout 5
```

### How the timeline is computed

- Only gap rows are scheduled. A `depends_on` predecessor that is not a
  gap (`openapi`) counts as done.
- Gap rows without `effort_days` are listed under `unestimated` and are
  not scheduled. A task that depends on one lists it in
  `waits_on_unestimated` and is scheduled as if it were done.
- Each department starts at day 0. Per task: earliest start and finish,
  and slack (how many days it can slip without moving the department's
  end).
- Tasks with zero slack form the department's critical path (red
  thread); `critical_path_days` is its length.
- `block` is `quick_ramp` when a task starts in the first 20% of the
  department's critical path length, otherwise `hardening`.
- The program length is the longest department critical path.
- A `depends_on` cycle makes that department fail with the names in the
  cycle.

### Output

```toml
failure = []

[program]
length_days = 17
critical_department = "Finance/Billing"

[[department]]
name = "Finance/Billing"
critical_path_days = 17
critical_path = ["Collect usage log", "Match usage to contract", "Create invoice"]
unestimated = [
    { process = "Dunning", sub_process = "Flag overdue invoices", current_interface = "none" },
]

[[department.task]]
process = "Invoice run"
sub_process = "Collect usage log"
current_interface = "file"
effort_days = 3
earliest_start = 0
earliest_finish = 3
slack_days = 0
critical = true
block = "quick_ramp"
waits_on_unestimated = []
```

`[[department.unestimated]]` entries are written inline as shown.
Departments that could not be loaded or scheduled appear as
`[[failure]]` entries with `department` and `reason`.

### Partial results

When some departments fail, the timeline for the others is still written
and each failure is printed as a `warning:` line on stderr:

```console
$ critical-path-timeline docs/examples/sources-partial.toml
# exit: 2
```

## 4. Exit codes

| Code | `gap-analysis-creator` | `critical-path-timeline` |
|---|---|---|
| 0 | gap table written | timeline written, all departments processed |
| 1 | input missing, not UTF-8, not TOML or invalid; invalid command line arguments | source list invalid, no department could be processed, or invalid command line arguments (e.g. `--timeout 0`) |
| 2 | - | timeline written, but some departments failed |

Output on stdout is always UTF-8, independent of the console encoding.
