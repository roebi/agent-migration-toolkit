# Process split worksheet

Department (`department`): ____________________
Parent process (`process`): ____________________

For each sub-process, fill one block. The names in backticks are the
field names in the department's process table (see
schema/process-table.schema.toml).

### Sub-process (`sub_process`): ____________________

- Input artifact, what comes in (`input_artifact`): ____________________
- Output artifact, what goes out (`output_artifact`): ____________________
- Interface to next sub-process (`interface_type`:
  openapi / file / manual / none): ____________________
- Automation grade today (`automation_grade`: full / partial / manual):
  ____________________
- Estimated working days to close the gap (`effort_days`), leave blank if
  unknown: ____________________
- Sub-processes of this department that must be done first
  (`depends_on`): ____________________
- Touches customer or license data? (yes/no, goes into `notes`):
  ____________________

Repeat this block for every sub-process identified in the parent
process form.
