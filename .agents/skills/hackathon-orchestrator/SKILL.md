---
name: hackathon-orchestrator
description: Orchestrate an unfamiliar hackathon task from intake through constraints, persistent Sol MAIN implementation, independent red teams, verification, and final no-AI explanation.
---

# Role topology

- Parent/default Terra = ORCHESTRATOR ONLY.
- Persistent Sol 6.1 = MAIN BUILDER and sole product-source writer.
- Terra = CODE RED reviewer, no edits.
- New independent Sol 6.1 = CONSTRAINT RED reviewer, no edits.
- Luna = RECORDER, no product-source edits.

Keep MAIN Sol's context when possible. Constraint Red must be independent.

# Phase 0 — before implementation

Have MAIN perform, in order:
1. task-router
2. problem-intake
3. constraint-discovery
4. data-profiler when data exists
5. tool-inventory when unfamiliar tooling exists

Do not implement until the Constraint Gate is complete.

# Constraint Gate

Require:
- explicit hard/soft constraints
- implicit reality candidates
- resource/cost/time/capacity/physical limits
- human burden and fairness
- persistence/retry/duplicate/idempotency risks
- extreme values and objective loopholes

Do not invent unstated numeric thresholds. Turn them into questions or soft candidates.

# Build loop

MAIN implements the smallest end-to-end happy path first.
At meaningful checkpoints:
- run Terra Code Red
- run Luna Recorder

After the first real end-to-end result:
- run an independent Sol Constraint Red using original requirements, data summary, and result metrics

Return findings to MAIN. MAIN alone fixes and integrates.

# Finish

15–20 minutes before submission:
- stop feature expansion
- final Code Red
- final Constraint Red
- final Recorder
- MAIN runs final-explain
- quiz the user one item at a time and correct only mistakes
