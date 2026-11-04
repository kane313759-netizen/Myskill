---
name: followup-prep
description: Prepare the participant for the official 6-question no-AI written follow-up by mapping actual work evidence to broad question families and generating concise practice questions without inventing events.
---

Read first:
- .hackathon-kit/EXAM_POLICY.md
- .hackathon-kit/run/GRADER.md
- .hackathon-kit/run/BASELINE.md
- .hackathon-kit/run/CONSTRAINTS.md
- .hackathon-kit/run/DECISIONS.md
- .hackathon-kit/run/VERIFY.md
- .hackathon-kit/run/SYSTEM_MAP.md
- .hackathon-kit/run/HUMAN_JUDGMENT.md
- .hackathon-kit/run/EDGE_CASES.md
- .hackathon-kit/run/AI_FAILURES.md
- .hackathon-kit/run/LIMITATIONS.md

The official follow-up is 6 questions × 5 minutes and must be answered without AI/copy-paste. Exact questions are unknown. All work in this skill happens during task solving, before the no-AI phase.
Read `.hackathon-kit/references/followup-question-bank.md` when present.

Follow note citations to the original task, code/config, captured commands/results, and actual participant answers. MAIN/Recorder/Tutor summaries are claims until their evidence is checked. Do not require a storage, web, container, or external-service answer for a task without that component.

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
- If no AI failure or material human-judgment event is recorded, say so honestly. Use another example only when that event actually happened and answers the question; do not manufacture a challenge to fill a template.
- A prevented edge case is valid even if it never became a bug.
- Only call something "my decision" when the participant actually decided/challenged/verified it.
- Separate automated verification from user-performed manual verification.
- Distinguish observed official-visible metrics from local declared-check coverage. Explain baseline-to-final progress only for the same rubric/checker and known input/policy/options scope; a local maximum does not predict hidden grades or prove that unrun checks passed.
- A question, acknowledgement, or restatement in the Tutor session is not by itself a manual check or a material human decision.
- Distinguish "no failure recorded", "a failure was resolved", and "an unresolved failure remains". Do not infer the first from the second.
- Model/role explanations must describe the actual verified runtime and workflow, not merely preferred model labels.
- If evidence is missing, say UNANSWERABLE FROM CURRENT RECORDS and identify what evidence would be needed.

# Six-axis compression

Compress evidence into:
A. What did we build?
B. Why this design/approach?
C. How did we use AI?
D. What did the participant personally judge/do?
E. How did we know it was correct?
F. What are the boundaries/limitations?

# CP2 — build coverage without interrupting implementation

Provide the six-axis evidence outline to Recorder at the first working end-to-end checkpoint. Recorder alone writes FOLLOWUP_CHEATSHEET.md and other explanation notes. Each axis needs a short claim plus a source/result or an explicit UNKNOWN / UNVERIFIED / UNANSWERABLE FROM CURRENT RECORDS. Empty human-judgment and AI-failure records are valid. Do not quiz the participant during routine implementation.

MAIN sends material changed decisions, actual participant actions, and transient failed-command evidence to Recorder as they occur; preserve useful command output before a retry overwrites it. Record meaningful events, not every routine edit or command.

# CP3 — one final coverage pass and bounded rehearsal

1. Use the orchestrator's submission deadline and reserved verification/submission time. Never extend the task's maximum 180 minutes to finish practice. If the remaining time is unknown, return the compact coverage first and avoid a waiting rehearsal until a budget is established.
2. Refresh only changed facts against current code/results and the latest actual review dispositions. If a late clarification/fix/review occurs after preparation, update affected outlines through Recorder before submission; do not restart the full quiz. Keep historical observations separate from their current resolution status. Return updates to Recorder rather than writing notes concurrently.
3. Select 6 actual hard/high-risk question families once for this task, spanning the six axes where useful. These are preparation choices, not predictions of the official questions. Give each a concise evidence-backed answer outline or mark the missing evidence explicitly.
   Across the delivered explanation/outlines, include the two `final-explain`
   evidence anchors: actual baseline-to-current observations with comparability
   limits, and one real retained/excluded or relevant validation/boundary case with
   its decisive rule and observed result. Use the existing facts; do not substitute
   general rules, a bug-name list, or internal notes for the case actually explained.
   If evidence is unavailable, deliver that limitation and reason explicitly.
4. `followup-prep` is the sole quiz owner. If time remains after required checks/submission work, ask short questions one at a time, prioritizing the participant's largest understanding gaps. Reuse the six selected families; do not launch a second quiz through `final-explain` or repeat completed rounds.
5. Correct only missing/incorrect facts. Use problem → AI action → human judgment → verification → result/limitation when relevant; omit parts unsupported by the evidence or unnecessary for the question.
6. Keep an answer short enough to type within the official 5-minute limit. Preparing six outlines does not require a full 6 × 5-minute simulation before submission. Stop rehearsal at the reserved submission boundary, even if not all six have been spoken through.
