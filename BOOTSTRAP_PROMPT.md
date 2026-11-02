# 시험 시작 프롬프트

Codex 첫 메시지로 사용:

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first.

Keep the current Terra session as ORCHESTRATOR only; it must not edit product source.
Create one Sol 6.1 MAIN BUILDER if that model is actually available, and let MAIN own problem understanding, specification, design, implementation, integration, difficult fixes, and final explanation.
Only MAIN edits product source.

Before implementation, MAIN must:
1. inspect grading/submission rules and existing tests/samples,
2. record a pre-edit build/test baseline,
3. identify high-risk/immutable contracts,
4. classify the task,
5. extract explicit constraints and separate assumptions,
6. prepare a short spec draft.

Do not implement product logic until CP1:
a fresh independent Constraint Red reviews the spec against original task evidence,
and .hackathon-kit/run/STATE.md records constraint_gate: CLOSED.

Use exactly these planned checkpoints:
CP1 SPEC FREEZE: independent Constraint Red.
CP2 FIRST END-TO-END: fresh Code Red + Recorder; Constraint Red only if the task/risk warrants it.
CP3 PRE-SUBMIT: fresh Code Red + fresh Constraint Red + Recorder + verification + final-explain.

During implementation, do not stop after every change to quiz me.
Record explanation notes automatically. Ask me only questions that materially affect score, feasibility, or an explicit business rule.
If no answer is available and it is safe to continue, record ASSUMPTION and choose a conservative reversible path.

For this exam:
- Computer Use / automated UI control is prohibited at every stage.
- external AI/model connections are prohibited.
- problem/files/results must not be transmitted externally.
- Git Push is prohibited.
- public GitHub tools and public Skills/MCPs/Plugins may be downloaded subject to those restrictions.
- follow-up written answers must be completed by me without AI/copy-paste.

15–20 minutes before submission, stop feature expansion and prepare me for the no-AI follow-up using only actual code, tests, task evidence, business-contact answers, and things I directly verified.
```
