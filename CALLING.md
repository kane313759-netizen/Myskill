# Quick calling guide

## 0. Install outside the task repo

```bash
KIT_DIR="$(mktemp -d)"
git clone --depth 1 https://github.com/kane313759-netizen/Myskill.git "$KIT_DIR"
bash "$KIT_DIR/install.sh" .
```

## 1. Start

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first.
Start with grader-intake and baseline.
Do not implement product logic until CP1 Spec Freeze closes the constraint gate.
```

## 2. CP1 — Spec Freeze

```text
Create a fresh independent Constraint Red review using
.hackathon-kit/prompts/CONSTRAINT_RED.md.
Give it original task/grading/test paths, GRADER.md, IMMUTABLES.md,
data profile if any, and SPEC_DRAFT.md.
Do not give DECISIONS.md as facts.
```

## 3. CP2 — First end-to-end

```text
Create a fresh Code Red using .hackathon-kit/prompts/CODE_RED.md.
Then run Recorder using .hackathon-kit/prompts/RECORDER.md.
Run another Constraint Red only if CP1 left material assumptions,
the task is optimization/operations-like, or result metrics show a constraint/realism risk.
```

## 4. Repeated failure

```text
Use .hackathon-kit/prompts/ESCALATE_SOL.md for a fresh analysis.
MAIN remains the only product-source writer.
```

## 5. CP3 — Pre-submit

```text
Stop adding features.
Run final fresh Code Red and fresh Constraint Red.
Finalize Recorder notes.
Use verification and final-explain.
Prepare me for the official no-AI follow-up using only actual evidence.
```

## 6. Doctor

```bash
bash .hackathon-kit/scripts/doctor.sh
```

## 7. Optional cleanup

Only if submission rules require helper files to be absent:

```bash
bash .hackathon-kit/scripts/clean.sh --apply
```

## One-line memory

**grader → baseline → spec attack → MAIN builds → code attack → final attack → explain**
