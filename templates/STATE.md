# RUN STATE

- phase: INTAKE
- task_types: UNKNOWN
- grader_contract: NOT_INSPECTED
- baseline: NOT_RUN
- immutable_inventory: NOT_RUN
- constraint_gate: OPEN
- cp1_constraint_red: NOT_RUN
- checkpoint: 0/3
- current_main: ACTIVE
- followup_prep: NOT_STARTED

## Open questions
- none recorded

## Assumptions
- none recorded

## Residual risks
- none recorded

## Gate close requirements
- grader_contract = RECORDED or UNKNOWN_AFTER_INSPECTION
- baseline = RECORDED or UNAVAILABLE_WITH_REASON
- immutable_inventory = RECORDED
- explicit constraints have evidence
- material unanswered items are answered or explicitly recorded as ASSUMPTION
- cp1_constraint_red = DONE
- then constraint_gate may be set CLOSED
