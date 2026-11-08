---
name: grader-intake
description: Discover the exam task's grading/submission contract and record a safe pre-edit baseline during the shared intake pass.
---

For confirmed finals or finals practice, use the corresponding section of
`hackathon-finals` under FINALS_POLICY.md instead of the preliminary procedure below.
Do not inherit the preliminary role, gate or six-question rules into finals.

Read `.hackathon-kit/EXAM_POLICY.md` first. Fill the installed templates without renaming the required section headings; MAIN runs the read-only gate `--preflight` before independent review. Follow the ownership/checkpoint protocol in `hackathon-orchestrator`; MAIN reports intake outcomes and never writes STATE/gate records.

# One evidence pass

Determine what success means before solving the business problem. Inspect original task/README/specification and submission rules first, then available tests/grading scripts, sample I/O, schemas/public interfaces, manifests/runtime configuration, and existing build/run commands. Share these observations with immutable-inventory, task-router, problem-intake, and constraint-discovery; do not rescan everything for each skill.

Batch-write `.hackathon-kit/run/GRADER.md` with:
- grading target, required output paths/files and run/build/submission commands
- visible tests/samples and original evidence paths/locations
- likely hidden contracts labeled INFERENCE
- time/memory/network/runtime/tool constraints
- protected interfaces/files and material scoring unknowns

Keep the official exam format intact when the task domain is unknown. Never replace official requirements with generic hackathon conventions. For UI/chat-only sources, preserve provenance-marked verbatim original/participant/Cofa excerpts in TASK_EVIDENCE.md separately from AI interpretation.

# Safe pre-edit baseline

Before executing a provided command, inspect its scripts/configuration for generated or modified files, destructive actions, dependency hooks, network requests, external uploads/telemetry, and service/database effects. A command named "test" is not automatically safe. Respect the ban on external task-data transmission, external AI connections, Git Push, and automated UI control.

Select the strongest relevant safe existing checks that fit the remaining task time, including implementation, independent review, repair, submission, and six-question preparation. Use an appropriate timeout/row/workload bound and isolate temporary outputs/state where needed. Do not start an unbounded expensive build/training/full-data job merely to obtain a baseline. Public-tool downloads remain allowed under the brief; no task files/results may accompany them.

Record exact commands, working directory, chosen bounds, relevant outcomes/exit status, existing failures, and local evidence/log paths in BASELINE.md before product edits. If a check is unsafe, missing, unavailable, or exceeds the available budget, record inspected sources and the concrete reason it was not run. Do not call an unrun check passing, weaken/delete tests, or repeatedly rerun a known baseline without a relevant change.

Use `.hackathon-kit/references/local-evaluation.md` within this same pass to make
baseline-to-final progress measurable. Prefer the existing visible grader; otherwise
build only small useful requirement-backed checks within the budget. Record the
visible native metric separately from local declared-check coverage, without invented
official weights. Bind actual rubric/checker/fixture hashes in GRADER or SPEC and
baseline report/version/input-policy-options scope in BASELINE for normal CP1 review.
`local_score.py` only summarizes evidence records; it does not run or approve tests.
Unknown or skipped checks never earn passing points, and unavailable scoring does
not justify a fabricated baseline or an additional implementation gate.

Completion means the contract is recorded or UNKNOWN_AFTER_INSPECTION with inspected sources, and the baseline is RECORDED or UNAVAILABLE_WITH_REASON with an actual explanation. ORCHESTRATOR records these outcomes in STATE; these labels alone are not gate approval. Freeze intake artifacts after CP1; send routine later results to Recorder for VERIFY.md.
