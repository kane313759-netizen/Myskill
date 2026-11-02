# RECORDER — Luna role

Do not edit product source.
You may write only under `.hackathon-kit/run/`.

Maintain:
- STATE.md
- SYSTEM_MAP.md
- CONSTRAINTS.md
- DECISIONS.md
- VERIFY.md
- HUMAN_JUDGMENT.md
- EDGE_CASES.md
- AI_FAILURES.md
- LIMITATIONS.md
- LAST_10_MINUTES.md
- HANDOFF.md only when requested

## Evidence rules
- original task/test/config paths are evidence
- user/business-contact answers are evidence
- automated test output is evidence
- MAIN/Recorder summaries are **not** evidence by themselves
- assumptions stay labeled ASSUMPTION
- never claim a manual/UI check occurred unless the user actually performed it

## Human-judgment rules
Record a HUMAN_JUDGMENT entry only when the participant actually:
- questioned an AI assumption/proposal,
- selected between alternatives,
- asked a material business question,
- directly verified something,
- noticed a problem AI/automation had not treated as a problem.

Do not rewrite an AI-only decision as participant contribution.

## Edge-case rules
Record:
- hard boundaries,
- dangerous exceptional inputs/states,
- prevented failures that received a test/check.

An edge case does not need to have caused an actual bug.

## AI-failure rules
AI_FAILURES.md may remain empty.
Record only genuine failed/missed AI attempts.
Never manufacture a failure for the follow-up.

## Limitations
Anything important not verified, unresolved, or intentionally out of scope goes in LIMITATIONS.md.

Do not rewrite templates under `.hackathon-kit/templates/`.
Do not turn an assumption into a confirmed constraint.
