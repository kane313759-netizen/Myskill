# Changes

## 2026-11-02-operational-r6

- task-router now selects optional helpers from original task evidence in the existing
  intake pass. Existing tools/NONE are preferred; narrow local modes, provenance,
  data/side-effect guards, fallbacks and budget go into the existing CP1 spec review.
- Added a bounded stdlib PATH inventory that never runs candidates, probes packages,
  installs or approves tools. Presence is explicitly unverified.
- Added task-conditional local-tool/reference guidance, exact-value/ID preservation,
  full secret redaction, no automatic extensions/fixes/hooks, isolated acquisition,
  and ordinary reopen/submission rules. No upstream runtime or new AI is bundled.
- Existing roles/checkpoints and EXAM_POLICY.md remain unchanged. Tool selection is
  an instruction/evidence workflow, not an OS/network enforcement sandbox.
- Validation: 83 local tests, targeted independent review and ten actual-agent
  decision replays; scope and untested runtime paths are recorded in
  [tool-selection-validation.md](references/tool-selection-validation.md).

## 2026-11-02-operational-r5

- A local nondeveloper simulation exposed gaps between prepared evidence and the
  explanation actually delivered to the participant. Clarified final explanation
  coverage for real task components, changed/preserved behavior, and expressly
  excluded preferences.
- CP3 now checks delivery of the existing explanation and six outlines before
  preparation is complete. No new checkpoint, per-step teach-back, second quiz,
  unconditional container requirement, or extension of the submission deadline.
- The full integrated simulation used r4. These later explanation clarifications
  do not retroactively change that run's answers, criteria, or results.
- EXAM_POLICY.md remains byte-for-byte unchanged.

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
