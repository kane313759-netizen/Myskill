---
name: followup-prep
description: Prepare the participant for the official 6-question no-AI written follow-up by mapping actual work evidence to broad question families and generating concise practice questions without inventing events.
---

Read first:
- .hackathon-kit/EXAM_POLICY.md
- .hackathon-kit/run/GRADER.md
- .hackathon-kit/run/CONSTRAINTS.md
- .hackathon-kit/run/DECISIONS.md
- .hackathon-kit/run/VERIFY.md
- .hackathon-kit/run/SYSTEM_MAP.md
- .hackathon-kit/run/HUMAN_JUDGMENT.md
- .hackathon-kit/run/EDGE_CASES.md
- .hackathon-kit/run/AI_FAILURES.md
- .hackathon-kit/run/LIMITATIONS.md

The official follow-up is 6 questions × 5 minutes and must be answered without AI/copy-paste. Exact questions are unknown.
Read `.hackathon-kit/references/followup-question-bank.md` when present.

# Question families

Map the actual work to these families:

1. problem / user / business need
2. scoring / success criteria
3. most important requirements
4. hard/soft/implicit constraints
5. hardest edge case
6. unstated-but-relevant risk
7. something AI initially missed
8. something AI could not solve directly
9. participant's own contribution/judgment
10. how AI was used
11. why each model/role was chosen
12. prompt/agent strategy
13. input → processing → storage → output → external
14. system boundary
15. storage/persistence
16. technology/tool choice
17. testing/verification
18. debugging/root cause
19. trade-off/alternative
20. limitation / what would improve with more time

# Truth rules

- Do not invent a failure just to answer an AI-failure question.
- If AI solved everything, answer honestly and use a real human-judgment case instead.
- A prevented edge case is valid even if it never became a bug.
- Only call something "my decision" when the participant actually decided/challenged/verified it.
- Separate automated verification from user-performed manual verification.
- If evidence is missing, say UNANSWERABLE FROM CURRENT RECORDS and identify what evidence would be needed.

# Six-axis compression

Compress evidence into:
A. What did we build?
B. Why this design/approach?
C. How did we use AI?
D. What did the participant personally judge/do?
E. How did we know it was correct?
F. What are the boundaries/limitations?

# Practice

Before submission:
1. Generate a compact FOLLOWUP_CHEATSHEET.md from evidence only.
2. Select the 6 hardest/highest-risk question families for this exact task.
3. Ask one practice question at a time.
4. Evaluate using:
   problem → AI action → human judgment → verification → result/limitation
5. Keep the corrected answer short enough to type within 5 minutes.
