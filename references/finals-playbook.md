# Finals task lanes and nondeveloper delivery

Used by `hackathon-finals` after reading the actual task. These are conditional
decision aids, not predictions or extra grading criteria. Use only relevant lanes;
do not load all domain skills or install a tool catalog by default.

## Choose from the required output

| Evidence in task | First complete path | Consequential checks before improving |
|---|---|---|
| Exact CLI/files/schema or existing failing app | Follow the interface; implement/fix the smallest required operation | Exact schema/encoding/order, malformed input, protected tests, actual run result |
| Tables, aggregates, report | Parse supplied data and compute required fields | IDs/joins, duplicate/null semantics, units, row counts, reconciliation; do not turn missing into zero without evidence |
| Prediction target and evaluation metric | Fit a simple permitted model; save predictions in required schema | Split by time/lot/tool/group when task requires it; prevent target/future/group leakage; fit preprocessing on training only; preserve held-out evaluation and metric direction |
| Resource assignment/schedule under constraints | Produce a feasible simple allocation and evaluate it | Capacity/route/time constraints, unassigned items and objective/tie order; do not invent fairness or weighted penalties |
| Documents/logs with source-grounded answers/actions | Extract/index relevant evidence and return cited answers or bounded classifications | Source coverage, conflicting/missing evidence, abstention and unsupported actions; run-time LLM/network use requires permission |
| UI/API/workflow deliverable | Complete one real user operation with the required state/output | Invalid input, persistence/restart, retries/duplicates and authorization only where relevant; test UI when permitted/available, otherwise mark it unverified |

Domain skills such as `ml-data-science`, `optimization`, `algorithm-cli`,
`document-processing` and `web-app` can supply task-specific checks when their
activation evidence exists. Their recommendations never add official rules.
For finals, do not invoke second-preliminary `grader-intake`, `problem-intake`,
`constraint-discovery`, `immutable-inventory`, `verification`, `final-explain` or
`followup-prep` procedures: their policy/roles are preliminary-specific. Use the
corresponding intake/check/explanation sections of `hackathon-finals` instead.

## Compare useful results

An acceptable comparison names the candidate versions, same data or split,
evaluator/metric, execution options and actual observations. Keep metric direction
and units explicit. When these differ, report results separately without a delta.
Use actual logs/outputs; a recorded number without an executed check is a claim.
One good aggregate may conceal catastrophic failures: inspect relevant hard
constraints and a concrete case, without inventing new score terms.

If runtime/compute is unknown, first bound a small diagnostic run. Do not train a
large model to discover that the final output path is missing. Missing external
API permission blocks that API route; it does not block a permitted local parser
or baseline. An official ban does not expire when the deadline approaches.

## Keep the participant informed without handing them engineering

Good progress: "입력 파일은 읽혔고 필수 결과 파일도 생성됐습니다. 현재 12개
공개 사례 중 10개가 맞습니다. 실패한 두 사례의 날짜 경계를 수정하겠습니다."
Use this wording only with actual observed results; it is an illustrative style.

Do not ask "어떤 모델/DB/프레임워크를 쓸까요?" when the task can decide it.
If an official ambiguity matters, say exactly which operation needs clarification
and why; offer one concise question for the participant to ask staff. Never send
it yourself without authorization. Do not repeatedly ask whether to continue.
Explain participant business choices in terms of outcome, cost or correctness.

The final explanation should let a nondeveloper describe the actual work:

- What was difficult and what this result does.
- What data enters and what usable output comes out.
- Why this approach fits the confirmed requirements.
- What changed relative to a comparable baseline, or why comparison is unavailable.
- One real case: relevant input, controlling rule, observed output and its meaning.
- What was tested, what can still fail, and the next human submission/demo action.

Do not force a slide deck, dashboard, live LLM, recorded failure, human contribution
or unsupported production ROI. Pitch claims must match the verified candidate;
synthetic demonstration results are not factory validation or official scores.

## Time and collection

The event notice's window is context, not a verified per-task deadline. Use an
observed clock and official task cutoff, reserve checks/repair/collection time and
adapt estimates to runtime and task complexity. If beginning late, reduce scope
rather than compress required checks to zero. On a long failure, stop, preserve
the last working path and choose the best remaining change. Work during lunch,
transition extensions, retries, separate follow-up and slide deadlines need their
own official evidence.

Before freeze, reconcile the actual candidate and output with final evidence.
List the real collection scope; do not infer exclusion from a partial preview or
`.gitignore`. Keep explanatory/internal records only where permitted by that
scope. Existing cleanup uses a local backup and ownership checks; do not manually
delete unknown task files. Verify required outputs remain after cleanup. After
freeze do not edit artifacts to match a later score or corrected explanation.
