---
name: verification
description: Verify the current scoring contract, constraints, regressions, and relevant boundaries against the recorded pre-edit baseline.
---

Read `.hackathon-kit/EXAM_POLICY.md` and .hackathon-kit/run/GRADER.md, BASELINE.md, IMMUTABLES.md, CONSTRAINTS.md. Use the checkpoint/ownership protocol in `hackathon-orchestrator`; MAIN verifies and reports evidence, Recorder writes VERIFY/LIMITATIONS, and ORCHESTRATOR alone writes STATE/gate/checkpoint records.

Start from safe relevant existing test/build commands and compare against BASELINE. Inspect changed command behavior for side effects/network use before running it. Bound checks to the remaining deadline and isolate temporary data/services; avoid duplicate full runs unless changes or failures justify them.

Check applicable scoring/sample contracts, confirmed hard constraints, normal/boundary/invalid inputs, duplicate/retry behavior, persistence/restart, integration boundaries, performance/precision/reproducibility, and domain sanity only for selected playbooks. Do not add domain requirements unsupported by the task.

Send factual results and evidence/log paths to Recorder for VERIFY.md; every important hard constraint has verification evidence or UNVERIFIED status. Distinguish automated checks from participant-performed manual checks. Preserve exact failures and unavailable-check reasons in LIMITATIONS rather than claiming coverage. Do not edit frozen intake artifacts for routine test updates.

Follow `.hackathon-kit/references/local-evaluation.md` for comparable baseline, CP2 and final local
coverage. Reuse frozen rubric/checker/oracle semantics and the same known dataset,
effective policy and execution bounds; record actual evaluated source hashes. Use
`local_score.py --compare` on retained evidence when helpful, without treating its
coverage as official score or proof that tests ran. Preserve native metrics separately.
Changed semantics/scope start a new series with no claimed delta; never overwrite the
baseline or weaken criteria. Cheap affected checks can track meaningful edits; do not
repeat expensive full-data checks after each edit. A local maximum cannot waive an
unverified hard rule, P0/P1 or the existing CP3 requirements.

At CP3, verify fixes/disproofs for all blocking Code Red/Constraint Red findings against the current files. P0/P1 OPEN or ACCEPTED_RISK findings cannot authorize submission. If the deadline limits repair, choose a valid smaller/partial solution and verify it; do not waive an official prohibition or submission-blocking conflict. Report dispositions to ORCHESTRATOR. A material spec/requirement change also requires renewed CP1 evidence/gate approval.

Never weaken/delete/skip tests merely to obtain green, hard-code samples, replace the submission wholesale with external code, claim manual checks the participant did not perform, or use Computer Use/automated UI control. No external task-data transmission, external AI connection, or Git Push. For UI/submission uncertainty use Cofa Helper through the participant; mark unverified UI behavior honestly.
