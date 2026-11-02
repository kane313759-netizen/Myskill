---
name: problem-intake
description: Explain the task and user value before coding, while separating confirmed facts, unknowns, and non-goals without blocking implementation on repeated user teach-back.
---

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

For unclear rules:
- mark OPEN QUESTION
- cite task/test/config evidence already checked
- ask only if the answer materially changes scoring, feasibility, or a required business rule

Do not stop implementation for user teach-back here.
Recorder should accumulate explanation notes; interactive explanation practice happens in final-explain before submission.
