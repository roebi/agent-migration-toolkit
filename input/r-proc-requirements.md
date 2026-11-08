# R-PROC requirement group

Runs first in Phase 0, in parallel with the R-CTRL workshop.

- R-PROC-001: process inventory - collect all existing processes per
  department.
- R-PROC-002: decomposition - split each process into sub-processes.
- R-PROC-003: automation grade classification per sub-process - full,
  partial, or manual.
- R-PROC-004: gap analysis - Ist-interface vs a clean OpenAPI contract,
  per sub-process. Extended scope: not just automation grade gaps, but
  artifact and interface gaps specifically.
- R-PROC-005: process table - the department x sub-process x grade x
  artifact x interface table; the deliverable of R-PROC-001 to 004.
- R-PROC-006: artifact definition (Ist) - input and output artifact,
  current format, per sub-process.
- R-PROC-007: interface definition (Ist) - the current handoff between
  two processes, including non-API/manual handoffs; turns a sub-process
  list into an actual process chain once gaps are closed.
- R-PROC-008: iteration loop - require, develop, test, deliver, then
  re-run the cycle as new features or processes surface.
