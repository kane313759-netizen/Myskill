# Independent review of a kit revision

Stage scope: r8 adds a separate finals profile under FINALS_POLICY.md and
`hackathon-finals`. For a finals change, read that profile and the supplied finals
notice/request as the current scope. Verify nondeveloper execution, conditional
task routing, unknown permission handling, truthful checks/delivery and installation
compatibility. The unchanged EXAM_POLICY.md and the fixed preliminary procedure
remain requirements for preliminary mode only. Do not impose their 180-minute,
six-question/model/Probe rules on finals or treat industry articles as exam rules.
In the template below, preserve the fixed format in its preliminary scope; it is
not a prohibition on the separately requested finals workflow. Review this public
kit in a clean context after modifications and relevant checks are complete.

Kit-maintenance handoff only. This is not an additional exam checkpoint or a
permission to transmit task files/results, use external AI, automate UI, or push
exam work. Review this public kit in a clean context before the exam.

Start a reviewer with no inherited conversation (`fork_turns="none"` where
supported), or a genuinely clean separate session. Record the exact candidate
commit/archive hash and comparison base. A new agent with inherited author history
is not independent. Give it original requirements and the candidate/diff, not the
author's reasoning or previous review votes. Keep review scratch outside the kit
checkout and task submission, within the actual permitted workspace.

For an offline handoff, include the comparison base's source as well as candidate
source and the diff; a base commit ID alone may be inaccessible to the reviewer.
Use a permitted local scratch path in the reviewer's environment. Paths from the
author's environment are references, not requirements to create or access them.

Copy this request, replacing the revision/path placeholders:

```text
Review this Myskill revision; do not edit it.
Candidate: <exact commit/archive hash and local checkout path>
Comparison base: <exact base commit>
Read EXAM_POLICY.md first; newer official instructions win.
Read only this checkout's original policy, changed source files, relevant unchanged
callers/templates/tests and the provided diff. Scope searches to explicit paths;
do not enumerate other agents' scratch, prior reviews or unrelated task outputs.
Write your report only to <authorized review-output path outside the checkout>.

Check official-policy conflicts; evidence-backed implementation gates; role/history
independence; actual delivery of baseline/current observations and one real
rule-applied case; honest unavailable/non-comparable results; bounded time/capacity;
installation/package compatibility; and domain-conditional behavior.

Use concrete file/code/behavior evidence. Existing CI passes are not new findings
without a counterexample outside that coverage. Do not ask for a more generic
hackathon format, remove the fixed 180-minute/six-question no-AI rules, manufacture
human actions/failures, or add routine quizzes and approval loops.
Each surviving finding: severity, file:line, evidence/reproduction, actual risk,
minimum correction and verification. If none survives, list attempted attacks and
remaining unverified scope. State actual context isolation and any accidental
exposure; do not claim OS isolation or blind review you did not have.
```

Finish modifications and relevant checks before dispatching the candidate. If a
finding leads to a change, obtain a targeted recheck bound to the revised files;
do not silently refresh hashes on an old approval. A read-only instruction review
or preparation-only replay is not a second full hackathon simulation and cannot
retroactively change its historical scores or establish real human no-AI ability.
