---
name: hackathon-orchestrator
description: Orchestrate the SK hynix AI hackathon workflow from grader intake through one Sol MAIN, fixed review gates, verification, cleanup, and final no-AI follow-up preparation.
---

Read `.hackathon-kit/EXAM_POLICY.md` first. Official exam/task instructions always win.

# Roles

- ORCHESTRATOR: default Terra session. **No product-source edits.**
- MAIN_BUILDER: one persistent Sol 6.1 when available. Sole product-source writer.
- CODE_RED: fresh Terra review context. No product-source edits.
- CONSTRAINT_RED: fresh independent Sol 6.1 review context. No product-source edits.
- RECORDER: Luna when available. Writes only under `.hackathon-kit/run/`.

If a named model is unavailable, preserve the role separation and use the strongest allowed available substitute. Record the actual model.

# Phase 0 — intake, before implementation

Have MAIN perform:
1. `grader-intake`
2. `immutable-inventory`
3. `task-router`
4. `problem-intake`
5. `constraint-discovery`
6. data/tool playbooks only when relevant

Create `.hackathon-kit/run/STATE.md` from the template if missing.

Do not implement product logic while `constraint_gate: OPEN`.

# CP1 — SPEC FREEZE

Before implementation:
- MAIN writes a short spec draft under `.hackathon-kit/run/SPEC_DRAFT.md`.
- Spawn a **fresh independent CONSTRAINT_RED**.
- Reviewer reads original task/spec paths directly, plus GRADER.md, IMMUTABLES.md, data profile if present, and SPEC_DRAFT.md as the thing to attack.
- Do not provide MAIN's DECISIONS.md as facts.
- Reviewer returns up to 3 highest-impact attacks, or attempted attacks that did not succeed.

A constraint can become CONFIRMED only from original task evidence or an explicit user/business-contact answer.
Unanswered non-blocking items remain ASSUMPTION.
When the gate requirements in STATE.md are satisfied, set `constraint_gate: CLOSED`.

# Build

MAIN implements the smallest scoring-relevant end-to-end path first.
Do not weaken baseline tests or hard-code sample outputs.

User interaction must not block routine implementation:
- record questions/assumptions
- ask only material questions
- if no answer is available, use a conservative reversible ASSUMPTION and continue when safe
- do not repeatedly quiz the user during implementation

# CP2 — FIRST END-TO-END

When the first scoring-relevant path works:
- fresh CODE_RED reviews code/tests
- RECORDER updates run notes
- run CONSTRAINT_RED again only when the task is optimization/operations-like, CP1 left material assumptions, or result metrics expose a realism/constraint risk

CODE_RED dynamic tests must avoid colliding with MAIN: prefer static review and existing tests; if extra runtime tests are needed, use isolated temp data/ports when possible.

# CP3 — PRE-SUBMIT

15–20 minutes before submission:
- stop feature expansion
- final fresh CODE_RED
- final fresh CONSTRAINT_RED
- RECORDER finalizes run notes
- MAIN runs `verification`
- MAIN runs `final-explain`
- run `doctor`/cleanup checks as appropriate

Only now quiz the user for the no-AI follow-up. The official follow-up is why this step is mandatory.

# MAIN context replacement

Persistent MAIN is preferred, not sacred.
If context is saturated or repeated reasoning degrades:
- write `.hackathon-kit/run/HANDOFF.md`
- start a new allowed MAIN
- continue from evidence files, not memory

# Review cap

There are only 3 planned checkpoints above. Do not spawn review agents for every small edit.
Extra review is reserved for a new P0 risk, major architecture change, or repeated failure.
