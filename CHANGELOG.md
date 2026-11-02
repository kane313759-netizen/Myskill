# Changes

## 2026-11-02-operational-r4

- Ran three actual-agent synthetic operational trials with independent examiner checks,
  MAIN handoff, a mid-task constraint notice, read-only Tutor probes, six outlines,
  exact submission collection, doctor and cleanup. Scope/evidence limits are recorded in
  [operational-rehearsal.md](references/operational-rehearsal.md).
- Fixed an observed heading-only CP1 stall: preserve installed template headings and run
  read-only document preflight before independent review; full gate remains mandatory.
- Fixed the finalization protocol after a late review outcome: refresh affected evidence
  notes/cheatsheet and compare with the latest actual disposition before completion.
- Fresh MAIN/Recorder replays verified both corrections without product/state/receipt edits.
- Added the original brief's whole-exam cutoff/transition and submission-time planning details.
  EXAM_POLICY.md remains byte-for-byte unchanged.

## 2026-11-02-exam-safe-r3

Rebuilt from GitHub main 13cc6ab142b570a9bbd4506c4123d93801ff3e4f.
EXAM_POLICY.md is byte-for-byte unchanged. Official 180-minute solving, six 5-minute
no-AI/no-copy follow-up, model restrictions, no Computer Use/external transmission/Git Push remain.

- CP1 now requires substantive evidence, actual Red report, original source paths,
  reviewed artifact hashes and resolved/disproved blocking findings. A stale spec fails.
- One canonical ownership/checkpoint protocol: independent no-history reviewers;
  MAIN sole product writer, ORCHESTRATOR state/receipt owner, Recorder evidence owner,
  Tutor strictly read-only. All MAIN notes are claims against original evidence.
- Follow-up evidence starts at CP2. One practice owner prepares all six answer outlines
  and bounds rehearsal by submission time; no manufactured human judgment or AI failure.
- Shared cross-platform lifecycle verifies ownership and versions, protects local changes,
  handles nested/worktree Git exclusions and backs up notes before safe cleanup.
- Bounded data readers handle encoding boundaries, explicit record/sheet selection,
  missing-key counts, ID false positives and failure exit status. Log triage handles mixed summaries.
- Shallow inventory is a bounded aid. Flat deterministic packages exclude runtime data.
- Regression coverage extends the previous CI cases on Linux and Windows.

Review proposals were evaluated against code and the official scope. Multiple same-model sessions,
20 preparation families and exam-specific restrictions were retained. No arbitrary two-question
coverage cap, Tutor model downgrade, silent NULL reinterpretation or unsupported objective penalty
was introduced. Time overflow and missing human events were treated as risks to manage, not
as already-proven execution outcomes. Shared Git exclude rules are intentionally retained
on cleanup; they do not imply exclusion from workspace-snapshot submissions.
