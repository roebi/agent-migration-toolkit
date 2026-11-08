# Code Review Checklist

Review 1 - 2026-11-08 - reviewer: Claude agent (code-review-en) -
basis: requirements.md, architecture.md, src/, tests/ at 247a3eb.

## Requirements Coverage

All tests pass (131 after the fixes below).

| Requirement | Covered by test | Test passes | Notes |
|---|---|---|---|
| R-SCHEMA-001 | test_schema.py `test_parse_table_*` | yes | incl. invalid TOML, non-table entries |
| R-SCHEMA-002 | `test_validate_table_reports_each_missing_field_by_name` | yes | also non-string fields |
| R-SCHEMA-003 | `test_validate_table_*automation_grade*` | yes | |
| R-SCHEMA-004 | `test_validate_table_*interface_type*` | yes | |
| R-SCHEMA-005 | `test_validate_table_accepts_optional_free_text_fields` | yes | |
| R-SCHEMA-006 | `test_validate_table_*effort_days*` | yes | non-finite rejected after fix F-02 |
| R-SCHEMA-007 | `test_validate_table_*depends_on*` | yes | |
| R-SCHEMA-008 | `test_validate_table_*duplicate*`, `*same_sub_process_name*` | yes | |
| R-SCHEMA-009 | test_templates.py `test_schema_example_*` | yes | |
| R-SRC-001 | test_sources.py `test_parse_sources_reads_*`, `*_without_*`, `*_without_name_*` | yes | |
| R-SRC-002 | `test_parse_sources_requires_exactly_one_of_url_and_path` | yes | |
| R-SRC-003 | `test_parse_sources_rejects_*url*`, `test_redirect_*` | yes | redirects checked after fix F-03 |
| R-SRC-004 | `test_load_all_reads_path_relative_to_base_dir` | yes | |
| R-SRC-005 | `test_load_all_fetches_url_with_timeout`, `*timeout*`, `test_urllib_fetcher_*` | yes | |
| R-SRC-006 | `test_load_all_continues_after_failures_*`, `*network_error*` | yes | |
| R-SRC-007 | `test_load_all_rejects_table_of_other_department` | yes | |
| R-GAP-001 | test_gap.py `test_*openapi*`, `test_mixed_table_*` | yes | |
| R-GAP-002 | `test_gap_row_has_*`, `test_gap_row_carries_*` | yes | |
| R-GAP-003 | `test_gap_description_names_next_step_per_interface_type` | yes | |
| R-GAP-004 | test_cli.py `test_gap_main_writes_*` | yes | |
| R-GAP-005 | `test_gap_main_invalid_input_exits_1_with_one_line_error` | yes | 4 cases |
| R-TPL-001 | test_templates.py `test_template_exists` | yes | |
| R-TPL-002 | `test_split_worksheet_asks_for_field` | yes | |
| R-TPL-003 | `test_template_references_only_existing_files` | yes | |
| R-TIME-001 | test_timeline.py `test_build_timeline_schedules_*`, test_cli.py `test_timeline_main_all_*` | yes | |
| R-TIME-002 | `test_schedule_only_includes_gap_rows` | yes | |
| R-TIME-003 | `test_gap_without_effort_is_unestimated_*` | yes | |
| R-TIME-004 | `test_forward_and_backward_pass_*`, `test_tasks_are_scheduled_regardless_*` | yes | |
| R-TIME-005 | `test_zero_slack_*`, `test_critical_path_uses_float_tolerance`, `test_empty_department_*` | yes | |
| R-TIME-006 | `test_block_*` | yes | |
| R-TIME-007 | `test_build_timeline_program_*` | yes | |
| R-TIME-008 | `test_cycle_in_depends_on_*`, `test_find_cycle_*`, `*cycle_as_department_failure` | yes | |
| R-TIME-009 | test_cli.py `test_timeline_main_all_*`, `*_writes_output_file_*` | yes | |
| R-TIME-010 | `test_timeline_main_*exits_2*`, `*exits_1*`, `*invalid_source_list*` | yes | |
| R-DEPLOY-001 | test_package.py, `uv build` (wheel holds both scripts) | yes | |
| R-DEPLOY-002 | .github/workflows/ci.yml | not run | YAML valid; bandit + semgrep clean locally; needs GitHub remote (OQ-2) |
| R-DEPLOY-003 | .github/workflows/release.yml | not run | needs GitHub remote + PyPI trusted publisher (OQ-2) |
| R-DEPLOY-004 | Dockerfile, entrypoint.sh | not run | no podman in dev container |
| NFR-06 | `test_build_timeline_six_departments_of_200_rows_under_5_seconds` | yes | ~0.01 s |

## Architecture Compliance

- [x] Module structure matches architecture.md (synced at 247a3eb)
- [x] No module has more than one responsibility
- [x] Side effects are isolated per design (I/O only in sources.py and cli.py; fetcher injected)

## Test Quality

- [x] Every FR has at least one test
- [x] Tests use descriptive names
- [x] No test depends on execution order (pure functions, tmp_path, no globals)
- [x] Coverage >= 80% (100%, gate also in pyproject.toml)

## Security

- [x] No secrets, passwords, or tokens in code or tests
- [x] All external inputs are validated (process table, source list, URLs, redirects, --timeout)
- [x] No arbitrary code execution from user input (no subprocess/eval/exec)
- [x] bandit (high) and semgrep (p/python, error) clean

## Code Quality

- [x] No em-dashes or long-dashes in src/, tests/, templates/, schema/
- [x] No magic numbers - named constants (TOLERANCE, QUICK_RAMP_SHARE, DEFAULT_TIMEOUT, EXIT_PARTIAL)
- [x] No dead code
- [x] Functions are pure where possible
- [x] ruff check passes

## Required Fixes

1. F-01 `--timeout -1` crashed with a ValueError traceback (NFR-03) -
   src/agent_migration_toolkit/cli.py:51 - major - FIXED ab479ab
2. F-02 `effort_days = inf` accepted, slack became nan (R-SCHEMA-006) -
   src/agent_migration_toolkit/schema.py:100 - major - FIXED ab479ab
3. F-03 urllib followed redirects to any host (R-SRC-003) -
   src/agent_migration_toolkit/sources.py:55 - major - FIXED ab479ab
4. F-04 No README, no usage documentation; pyproject has no `readme`,
   so the PyPI page would be empty and department teams have no usage
   guide. Not covered by any requirement -> requirements gap, must go
   back through gather-requirements (proposed group R-DOC) -
   README.md / docs/ / pyproject.toml - major - OPEN
5. F-05 stdout output on Windows with a non-UTF-8 redirect could raise
   UnicodeEncodeError for non-Latin characters (NFR-02/03) -
   src/agent_migration_toolkit/cli.py:107 - minor - follow-up
6. F-06 source `path` may be absolute or leave the source list's
   directory; acceptable because the source list is the user's own
   local config, but should be documented - sources.py:99 - minor -
   document with F-04
7. F-07 several tests assert more than one property of the same result -
   tests/ - minor - accepted (one behaviour per test)
8. F-08 CHANGELOG.md (keepachangelog 1.1.0) does not exist yet - it is
   created by the release phase (release-sw-project-en) - minor - release

## Fix Log

| Date | Finding | Commit | Result |
|---|---|---|---|
| 2026-11-08 | F-01, F-02, F-03 | ab479ab | 8 new tests, 131 passing, coverage 100% |

## Result

```yaml
phase: review
status: blocked
output: review-checklist.md - 0 critical, 1 major open (F-04 docs gap), 4 minor
```
