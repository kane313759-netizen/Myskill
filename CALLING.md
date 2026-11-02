# Quick calling guide

Read EXAM_POLICY.md first. Canonical roles/checkpoints live in hackathon-orchestrator.
Use the README installation steps with a pre-exam verified SHA or frozen flat ZIP.

## Start

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first.
One evidence pass for grader intake, safe baseline, immutables, routing and constraints.
Include evidence-based optional-tool selection in that pass: existing tools/NONE first,
local guarded modes only, with the decision in SPEC's existing verification plan for CP1.
MAIN alone writes product source; ORCHESTRATOR alone writes STATE/gate/receipts.
Do not implement until independent CP1 review and gate_check pass.
```

## Optional second terminal — Tutor

Only when supported by the provided environment; Sol 6.1 preferred when available.

```text
Read .hackathon-kit/prompts/TUTOR.md and EXAM_POLICY.md.
You are strictly read-only, including run notes and commands.
Explain current code/evidence; do not decide or edit for MAIN.
```

During solving, forward an actual material personal question/choice/check to MAIN or Recorder
with evidence if it should be recorded. Tutor explanations alone are not personal verification.
No AI/copy-paste is used during the official follow-up itself.

## CP1 — Spec Freeze

```text
Create a new Constraint Red using prompts/CONSTRAINT_RED.md with no inherited conversation:
fork_turns="none" where supported, otherwise a clean separate session.
Send EXAM_POLICY and original task/grading/test paths before MAIN's draft artifacts.
Treat GRADER, IMMUTABLES and SPEC as claims to verify against originals.
Have MAIN preserve installed template headings and pass gate_check.py --preflight first.
The preflight checks document format only; it is not review approval.
Persist the actual report as CP1_RED.md and structured receipt as CP1_REVIEW.json.
Fix/disprove blocking findings with evidence and reviewer rechecks.
ORCHESTRATOR writes candidate CLOSED, runs the evidence gate, and restores OPEN on failure.
Only a passing check against current evidence authorizes implementation.
```

```bash
python .hackathon-kit/scripts/gate_check.py --artifact-hashes
python .hackathon-kit/scripts/gate_check.py
```

Hash output is a utility, not approval. Freeze the five reviewed documents after CP1;
reopen on material changes and obtain a targeted independent recheck.

## CP2 — First end-to-end

```text
Run clean Code Red using prompts/CODE_RED.md, then Recorder.
Update verification evidence and start six-axis FOLLOWUP_CHEATSHEET coverage.
Run Constraint Red again only for a material task/assumption/objective risk.
```

## Repeated failure

```text
Use prompts/ESCALATE_SOL.md for fresh analysis. MAIN remains the sole product writer.
Preserve useful failed-command evidence before a retry overwrites it.
```

## CP3 — Pre-submit

```text
Budget time for review, repair, checks, submission and preparation before the real deadline.
Stop features; run final clean Code Red and Constraint Red and resolve/recheck blockers.
Run verification; Recorder finalizes actual evidence.
Use final-explain for factual explanation, then followup-prep once for the six-question
FOLLOWUP_CHEATSHEET and a short rehearsal within the reserved time.
Record review/verification/followup completion in STATE via ORCHESTRATOR only.
Run doctor; cleanup is last, after prep, only if the submission format requires removal.
```

```bash
bash .hackathon-kit/scripts/doctor.sh --pre-submit
bash .hackathon-kit/scripts/clean.sh --apply
```

PowerShell: doctor.ps1 -PreSubmit / clean.ps1 -Apply. Cleanup's default is dry-run.
Git ignore is local status filtering, not directory-snapshot exclusion. Keep the printed local backup path.
