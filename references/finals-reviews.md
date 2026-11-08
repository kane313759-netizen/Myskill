# Finals independent review coverage and scheduling

The participant approved six core review roles and conditional SECURITY_RED on
2026-11-08. This is the kit's quality protocol, not a new official grading rule.
Current official stage rules and actual agent/tool permissions still take priority.
Do not import assumptions, fixed times or remote-backup permissions from the
separately reviewed universal v2.6 proposal.

## Common protocol

Use one product writer. Every independent role receives a new clean context,
original task/rule/evaluator sources, the exact candidate read set and its own
authorized scratch/report paths. Do not give author conversation or prior votes
as facts. A different role name on the same worker is not a separate review.
Reviewers do not edit product files, protected originals or shared records.

Follow `review-execution.md` for actual launch, worker activity and completed
report observations. Observe returned worker IDs; never certify a model/context
you cannot verify. Preserve reports, current code/config/evaluator/output hashes,
STATIC versus EXECUTED checks, unrun reasons, findings and actual fix rechecks.
Execution COMPLETE, review ACCEPTED and product/submission success differ.

Every finding names original evidence, concrete reproduction or static path,
expected/observed behavior, severity/impact and minimum correction. A useful
no-findings report lists attempted attacks and remaining limits. P0/P1 OPEN or
ACCEPTED_RISK does not satisfy acceptance; FIXED/DISPROVED needs verification.
Never invent task requirements, oracle scores, human actions or comprehension.

## Six core responsibilities

| Role | Input and responsibility | Boundary |
|---|---|---|
| CONSTRAINT_RED | Original requirements, allowed operations, objective/metric definitions, hard constraints and assumptions | Cannot establish unwritten factory policy; obtain official/owner evidence |
| DATA_EVAL_RED (`data-eval-redteam`) | Input identity/units/time/joins, missing-label/sampling risks, leakage and train/tune/final separation; independent positive/negative controls for the evaluator | Does not know hidden labels or invent official weights; absent statistics are NOT_APPLICABLE with reasons |
| ALGORITHM_RED (`algorithm-redteam`) | Formulation, algorithm/solver suitability, feasibility, objective arithmetic and optimality evidence; changed settings actually recomputed with current derived values/cache | Best-known search is not a proven optimum; compare each setting against its own valid oracle/bound |
| CODE_RED | Current implementation, I/O and interfaces, errors/state/retries, regressions and literal runnable commands | General code review does not replace another role's specialized report |
| EDGE_RED (`edge-redteam`) | Task-relevant boundaries, missing/null/empty/zero, malformed/duplicate/extreme cases and basic trust-boundary counterexamples | Does not certify every attack surface or perform unauthorized penetration testing |
| SUBMISSION_RED (`submission-redteam`) | Exact final collected files/config/version, reproducible execution where required, format/size/dependencies and collection exclusions | Does not upload/freeze or infer actual submission receipt from a prepared archive |

For CONSTRAINT_RED and CODE_RED in finals, dispatch from the responsibilities and
common protocol here plus FINALS_POLICY.md. Do not reuse preliminary prompts with
fixed EXAM_POLICY/model/CP1 assumptions. Task-conditional domain skills can supply
checks, not new official rules. An algorithm role on a task without optimization
reviews its actual transformations/decision logic and explicitly limits the
optimality topic; it does not force a solver into the product.

## SECURITY_RED trigger

Inspect actual original task sources and current implementation. Activate the
separate `security-redteam` reviewer when any evidenced condition applies:

- AUTH: login, identity, roles, object access or authorization is a task requirement
  or implemented boundary.
- EXTERNAL_ROUTE: a required/implemented externally reachable service, external
  API/AI integration, or transfer across a data-trust boundary.
- SECRETS: the solution actually handles credentials, tokens or keys.
- PRIVILEGED_TOOLS: untrusted input/documents can influence tool execution or
  consequential privileged actions (for example commands, remote writes or
  equipment actions), beyond ordinary bounded local output generation.
- SENSITIVE_DATA: actual personal/confidential data handling requires protected
  access, retention or transfer decisions.

Record the condition, original source path/current hash and exact supporting
excerpt. An installed SDK, available network tool, the word AI, hypothetical
future feature or semiconductor branding alone is not a trigger. Inspect the
route rather than inferring exposure from a technology name.

Record TRIGGERED, NOT_TRIGGERED with inspected evidence/reason, or UNKNOWN.
UNKNOWN is not a false negative: keep security review pending and investigate
the material gap while independent permitted work continues. Re-evaluate after a
material authentication, data-route, credential, privilege or dependency change.
Once triggered, SECURITY_RED is required for full quality completion; it cannot
be silently dropped at deadline. Static review may proceed when dynamic-test
permission is unknown, but unknown permission never authorizes the operation.
When not triggered, explicitly mark only SECURITY_RED NOT_APPLICABLE with reason.
EDGE_RED retains its basic relevant checks regardless of this trigger.

## Schedule without a permanent seven-agent roster

- Intake: CONSTRAINT_RED reviews the proposed contract before affected product
  implementation. DATA_EVAL_RED reviews original input semantics and evaluator
  controls before their numbers drive optimization or claims. Obtain required
  official answers rather than assuming a prohibition or hard constraint away.
- First working path: ALGORITHM_RED checks actual computation and settings;
  CODE_RED and separate EDGE_RED inspect implementation and counterexamples.
  SECURITY_RED inspects triggered surfaces before reliance on those operations.
- Changes: run cheap relevant regression checks after ordinary settings edits.
  New objective/constraints, unexplained output, materially changed algorithm,
  evaluation split or trust boundary requires affected clean review. Do not
  spawn all roles after every numeric adjustment or redo all intake by default.
- Final current candidate: complete the six core roles, plus SECURITY_RED if
  triggered, with clean final contexts and current scope-bound receipts. Stage
  them sequentially when capacity is limited; final SUBMISSION_RED works on the
  actual collected candidate after other fixes. It can find a blocker requiring
  a writer fix and affected review/replay before freeze. Never patch frozen files.

At a new checkpoint, use a fresh reviewer. A same-checkpoint reviewer may recheck
its own finding; retain original failure and actual targeted recheck evidence.
After a change, never rehash an old receipt into approval. Bind final acceptance
to actually reviewed current files, not the baseline or a report written early.
Do not allow six simultaneous workers to compete for source ownership or time.

If agents are unavailable or prohibited, mark the missing roles NOT_RUN and any
writer checks SELF_CHECK. Continue independent permitted work and show the gap
in Korean; do not ask the nondeveloper to debug agent controls. Do not claim full
independent quality completion. This kit does not invent a competition ban on a
valid partial/degraded submission; follow the official contract and disclose its
actual limitations. Known official violations cannot be waived as missing review.

## Aggregate current evidence

The writer/orchestrator maintains `run/FINALS_REVIEWS.json` from its installed
template and summarizes it in FINALS_RUN.md. Use a common `required_scope` of the
current relevant product source, configuration, evaluator and collected outputs;
each final receipt binds that scope plus any role-specific original evidence.
Large input data may be identified by a verified manifest; checking its manifest
file alone does not prove whole-data integrity unless the underlying hashes were
actually recomputed. Keep raw data and private histories outside reviewer reads
unless specifically required and authorized.

Record each final role ACCEPTED only after its actual completed receipt/report
and verified blocker dispositions. The security object retains current inspected
source hashes, exact trigger evidence or a supported non-trigger reason. Separate
worker IDs are required across roles at this checkpoint.
Reports also use separate canonical paths and role-specific content; copying one
report into multiple role entries (even under new filenames) is not accepted.
An active SECURITY_RED receipt also binds all current security inspection sources,
including original rule/route documents outside the common candidate scope;
changing the evidence cannot silently reuse a review of an earlier rule set.

```text
python .hackathon-kit/scripts/finals_review_check.py --checkpoint FINAL
```

The agent runs the command using the actual available Python executable; the
participant need not memorize it. The helper checks current hashes, per-role
execution records, distinct workers, recorded dispositions and security activation
consistency. It cannot authenticate records, discover every missing source file,
establish real optimality/security, infer a hidden score or confirm submission.
The official task's actual tests, independent review substance and human-only
submission steps remain necessary. After cleanup, retain permitted notes/receipts
using the existing ownership-safe local backup and check actual collected files.
