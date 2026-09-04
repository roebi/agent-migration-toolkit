# Glossary

- **Ist** - the current, as-is state of a process: what artifact exists
  today, in what format, and how it currently reaches the next process
  (including manual handoffs like email or spreadsheets).
- **Gap** - the distance between the Ist-interface and a clean OpenAPI
  contract. Every non-openapi `interface_type` in the process table is
  a gap row.
- **Automation grade** - full, partial, or manual. Describes how much
  of a sub-process currently runs without a human doing the work by
  hand.
- **Red line** - the non-negotiable governance rule, see red-line.md.
- **Red thread** - the critical path for one department's ramp to its
  agent-run target; independent of the other departments' red threads,
  but all share the same foundation (Red Line, R-CTRL, R-API gateway).
- **Quick ramp / hardening** - the two-block split of a department's
  runway: quick ramp is the first ~20% of time (rough automation of the
  obvious cases), hardening is the remaining ~80% (edge cases, audit
  trail, durable floor).
- **Process chain** - a sequence of sub-processes connected by defined
  artifact interfaces, where one sub-process's output artifact is the
  next one's input artifact.
