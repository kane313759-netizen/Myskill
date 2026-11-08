---
name: problem-intake
description: Explain the task and user value before coding, while separating confirmed facts, unknowns, and non-goals without blocking implementation on repeated user teach-back.
---

For confirmed finals or finals practice, use the corresponding section of
`hackathon-finals` under FINALS_POLICY.md instead of the preliminary procedure below.
Do not inherit the preliminary role, gate or six-question rules into finals.

Read `.hackathon-kit/EXAM_POLICY.md` and `.hackathon-kit/run/GRADER.md` first when present.

Explain concisely:
1. who/what uses the result
2. what problem is being solved
3. required input
4. required output
5. one normal example grounded in task material if available
6. one failure/hold/invalid example if supported
7. what a wrong result would break

Map only the components that actually exist:
input → processing → storage (if any) → output → external connections (if any)

Do not force web/backend/DB/Docker concepts onto tasks that do not have them.

When MAIN selects a material tool/algorithm, follow the active kit's
`references/participant-understanding.md` and explain its actual role, input/output,
selection reason, alternative and limits in plain Korean alongside implementation.
Do not wait for the nondeveloper to ask what an optimizer is or postpone all
method understanding until final submission; do not ask them to design it.

For unclear rules:
- mark OPEN QUESTION
- cite task/test/config evidence already checked
- ask only if the answer materially changes scoring, feasibility, or a required business rule

Do not stop implementation for user teach-back here.
Send concise source-linked problem facts and material participant answers to Recorder for the evidence notes. MAIN owns phase-0 task contracts; Recorder alone updates the explanation notes. Do not infer a participant decision or manual check merely because the participant asked a question.

Recorder starts the six-axis FOLLOWUP_CHEATSHEET at CP2 and updates changed evidence at CP3. `final-explain` supplies the factual explanation; `followup-prep` alone owns submission-time rehearsal. Do not postpone all evidence collection until the final 15–20 minutes.
