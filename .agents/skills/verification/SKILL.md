---
name: verification
description: Verify scoring contracts, confirmed constraints, regressions, persistence, and task-relevant edge cases against the recorded baseline.
---

Read:
- EXAM_POLICY.md
- GRADER.md
- BASELINE.md
- IMMUTABLES.md
- CONSTRAINTS.md

Start from the task's existing test/build commands and compare against BASELINE.

Minimum categories when applicable:
- visible grading/sample contract
- confirmed hard constraints
- normal case
- boundary case
- invalid/missing/conflicting input
- duplicate/retry/idempotency
- persistence/restart
- integration path
- task-specific performance/precision/reproducibility
- domain sanity only when the selected playbook calls for it

Rule: every important confirmed hard constraint should have evidence of verification or be marked UNVERIFIED.

Never:
- weaken/delete a test to get green
- hard-code visible samples as the solution
- claim browser/UI behavior was verified by Computer Use; Computer Use is prohibited in this exam
- claim a manual check occurred unless the user actually performed it
