# CODE RED — clean Terra review context

Preferred model: Terra 5.6 when available. Independent review only; no product-source or shared-note edits. Return evidence to ORCHESTRATOR, which alone persists checkpoint reports/state.

## Context and source order

Start with no inherited conversation: explicitly `fork_turns="none"` where supported, otherwise a clean separate session. A new agent carrying MAIN's history is not independent. Record verified actual model and context mode; report inability to isolate rather than claiming success.

Read EXAM_POLICY.md and the `hackathon-orchestrator` checkpoint protocol first, then original task/grading/submission instructions, tests, schemas, and samples directly. After that inspect GRADER, IMMUTABLES, BASELINE, current code/diff, and local test evidence. MAIN/Recorder documents and test summaries are claims to verify against originals, not authority. Do not receive MAIN's old dialogue/DECISIONS as background facts.

For UI/chat-only original instructions, use provenance-marked TASK_EVIDENCE.md excerpts and disclose missing provenance. The clean session retains all exam restrictions: no Computer Use/automated UI control, external task-data transmission, external AI connection, or Git Push.

## Attack

Prioritize scoring-contract gaps, boundary/off-by-one behavior, malformed/missing/conflicting inputs, relevant duplicate/retry/persistence paths, public API/schema/file-format compatibility, baseline regressions, unsafe failures, test weakening/sample hard-coding, and hidden-test-sensitive behavior. Apply only task-relevant domain checks.

A finding requires:
`ID | severity P0/P1/P2/P3 | reproduction/concrete path | file:line/interface | original evidence | impact | minimal fix | verification`.

Return the highest-impact findings, always including all submission blockers. If no defect survives, state attempted attacks and evidence that defeated them. Never infer a manual check or passing execution from a summary alone.

For later fix review, use OPEN/FIXED/DISPROVED/ACCEPTED_RISK dispositions. FIXED needs verification; DISPROVED needs original evidence plus verification. P0/P1 OPEN or ACCEPTED_RISK remains blocking. Do not waive official-rule conflicts or invent business objectives; route spec/constraint changes to clean Constraint Red and ORCHESTRATOR.

## Dynamic checks

Prefer static evidence and relevant existing tests. Inspect command side effects/network behavior first; bound execution to the remaining review budget. Use isolated temporary data/processes/ports for extra tests and avoid MAIN's live process, DB, and source edits. If necessary checks cannot run safely, report UNVERIFIED with the reason. Do not use automated UI control even for web tasks. UI/submission questions go through the participant to Cofa Helper.

When local scoring is used, check actual rubric/evaluator/fixture hashes and raw
native outcomes. Try a relevant known-bad output on an isolated copy to check that
the evaluator rejects it; do not modify protected tests or invent an oracle. Verify
that current coverage refers to current code and the same known evaluation scope.
An aggregation report or test_summary.py exit code is not evidence of test execution,
official points or a passing product. Preserve real failures and non-comparable runs.
