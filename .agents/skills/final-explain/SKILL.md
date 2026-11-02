---
name: final-explain
description: Prepare the participant for the official no-AI written follow-up using only actual task evidence, code, tests, decisions, and directly verified behavior.
---

This skill produces the factual system explanation at CP3. It does not run a quiz or invoke `followup-prep`; the orchestrator invokes that skill once.

Use:
- actual task/spec
- GRADER.md / BASELINE.md / CONSTRAINTS.md / DECISIONS.md / VERIFY.md
- current code/config
- business-contact answers
- things the user actually verified

Follow citations back to original evidence. A note or MAIN's summary alone does not establish a fact. Distinguish CONFIRMED / ASSUMPTION / UNVERIFIED; missing evidence is not a passing check.

Explain only components that exist:
1. problem solved
2. input
3. processing
4. storage/persistence if any
5. output
6. external connections if any
7. actual system boundaries
8. runtime/container only if present
9. important confirmed constraints
10. key design decisions and alternatives
11. what was verified
12. what remains unverified / limited

Compress to:
input → processing → storage(if any) → output → external(if any)

Return a concise explanation with source locations, verified results, and limitations to the orchestrator and Recorder. Recorder is the sole writer of explanation notes under `.hackathon-kit/run/`; do not race it with your own note edits.

The official follow-up is 6 questions × 5 minutes without AI/copy-paste. This explanation is preparation during task solving only. `followup-prep` owns any rehearsal within the remaining submission time.
