# Automation grade decision tree

Walk this for every sub-process marked "partial" or "manual" with a
defined output artifact.

1. Is the procedure the same every time regardless of input content
   (same clicks, same fields, same order)?
   - Yes -> candidate for a script/tool (deterministic, cheap,
     testable). Go to 2.
   - No, it needs judgment or varies by case -> candidate for an
     agent skill instead. Stop here, route to skill design.

2. Does the system already have an API?
   - Yes -> call it directly, no bridge needed.
   - No -> needs an OpenAPI bridge wrap (see the
     fx-app-control-orchestrator / transparent-openapi-mcp bridge
     patterns) before the script/tool can call it.

3. Does this sub-process touch customer or license data?
   - Yes -> stays under full R-CTRL gating regardless of how simple
     the algorithm is. Red Line applies.
   - No -> lighter R-CTRL tier is possible, confirm in the R-CTRL
     workshop.
