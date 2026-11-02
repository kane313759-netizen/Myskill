# RUN STATE

ORCHESTRATOR alone writes this file. Keep one line per status key.

- phase: INTAKE
- task_types: UNKNOWN
- grader_contract: NOT_INSPECTED
- baseline: NOT_RUN
- immutable_inventory: NOT_RUN
- constraint_gate: OPEN
- cp1_constraint_red: NOT_RUN
- cp3_code_red: NOT_RUN
- cp3_constraint_red: NOT_RUN
- verification: NOT_RUN
- checkpoint: 0/3
- current_main: ACTIVE
- followup_prep: NOT_STARTED
- submission_deadline_utc: UNKNOWN

## Open questions

## Assumptions

## Residual risks

## Gate close requirements
- grader_contract = RECORDED or UNKNOWN_AFTER_INSPECTION, with inspection evidence
- baseline = RECORDED or UNAVAILABLE_WITH_REASON, with commands/outcomes or reason
- immutable_inventory = RECORDED
- five phase-0 artifacts contain substantive evidence and required sections
- original task sources are recorded; UI/chat-only evidence has provenance
- independent CP1 report exists and its receipt binds all five reviewed artifact hashes
- P0/P1 findings are FIXED or DISPROVED with evidence and verification
- cp1_constraint_red = DONE; only then set constraint_gate = CLOSED and run gate_check.py
- freeze those artifacts after CP1; routine verification belongs in VERIFY.md
- reopen before material contract edits; fresh targeted Red recheck binds revised hashes

The checker validates supplied records. It cannot prove business truth, actual model identity,
or clean-context creation; ORCHESTRATOR must verify and record those honestly.
