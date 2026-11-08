---
name: hackathon-finals
description: Lead a nondeveloper through the SK hynix finals, choosing an evidence-backed solution and carrying out implementation, validation, explanation and submission preparation. Use for confirmed finals or finals practice, not the fixed second-preliminary workflow.
---

Read `.hackathon-kit/FINALS_POLICY.md` first. If reading the source checkout,
use its root `FINALS_POLICY.md`; do not install into the source checkout.
Read `.hackathon-kit/references/finals-playbook.md` for the applicable task lane.
Read `.hackathon-kit/references/finals-reviews.md` for the approved six core roles,
conditional SECURITY_RED, scheduling and final aggregate evidence check.
Use `templates/FINALS_RUN.md` from that same kit as the starting run record.
This is the canonical finals workflow; the second-preliminary orchestrator,
role prompts, STATE/gate receipts and six-question rehearsal are not its defaults.

## Own the technical work

The participant is a nondeveloper. Inspect available evidence and execute the
authorized work; do not give only advice, a study plan, commands to type, a list
of algorithms to choose from, or a request to design the system. Choose and
explain the smallest workable approach. Run commands and diagnose failures
yourself when tools permit. Do not silently downgrade a missing capability to a
pass or ask the participant to debug it. Give exact, brief manual actions only
for an actual human-only UI/identity step or a genuinely unavailable capability.

Ask only for missing official permissions/rules, access, or a material business
decision not answerable from task sources. State why the answer matters and
continue independent useful work. Routine technical choices, reversible fixes,
test selection and local record updates require no participant approval loop.
Show Korean plain-language progress: what works, what remains uncertain, what
you are doing next. Read `references/participant-understanding.md` in the same
kit and proactively explain each material actual tool/algorithm at selection,
after a consequential change, and in the final delivery. Include what it does,
input/output, why it fits, one alternative, an actual case and its limits.
Distinguish tool/library from algorithm and planned from actually executed use.
The participant should understand the choice without taking over engineering.
Never fabricate participant judgment, manual checks, failures or claimed learning.

## Select the stage and rules before execution

Recognize a confirmed finals request or explicit finals practice. If the stage
is ambiguous, inspect the supplied notice before asking. Record preparation,
practice or live competition; synthetic practice does not certify live readiness.
Read the latest official task/guide/portal excerpts available through permitted
means. Distinguish OFFICIAL (with source), PARTICIPANT_REPORT, ASSUMPTION and
UNKNOWN. Research articles and predicted problem domains are background only.
Use the profile's operation-specific uncertainty rule; do not infer network,
AI/model, prepared-file or multi-agent permission from this kit or a personal PC.

Read `references/review-execution.md` in the same kit. Delegate only if agents are available and current rules plus the user/task
instructions authorize it. Use one product writer. Clean reviewers receive
original task evidence and the scoped candidate, without author conversation;
record actual launch method/model if verified. Never claim a requested model
was selected. If clean review is unavailable, perform a separate self-check,
label it SELF_CHECK / independent review NOT_RUN and state the limitation.
Do not wait indefinitely, fake independence or block all progress just to fill
the preliminary's role roster. Required official checks still cannot be waived.
For each actual review, observe launch return/worker ID, running acknowledgement
and completed report tied to the current scope; keep the execution receipt.
Dispatch, a role label or a locally authored DONE is insufficient. Check launch
soon and handle failure/capacity yourself; do not wait for the participant to
discover that no worker ran. Distinguish execution COMPLETE from review ACCEPTED.

The core roles are CONSTRAINT_RED, DATA_EVAL_RED, ALGORITHM_RED, CODE_RED,
EDGE_RED and SUBMISSION_RED. Use the dedicated skills mapped in finals-reviews;
dispatch final Constraint/Code reviews from that finals protocol, not preliminary
role prompts. Use distinct clean workers per role, current scope-bound receipts
and actual report acceptance. Do not relabel one worker's report or the writer's
tests as multiple independent roles. Stage the reviews, not six always-on agents.

Inspect current task/project evidence for the SECURITY_RED conditions in that
reference. Record TRIGGERED, NOT_TRIGGERED with inspected evidence, or UNKNOWN;
available SDKs/tools and the word AI do not trigger it. When triggered, launch
separate `security-redteam` before relying on its affected operations and on the
final candidate. UNKNOWN cannot silently become a non-trigger. Missing review
stays NOT_RUN/SELF_CHECK and is disclosed, never full independent completion.

## Intake and plan — one evidence pass

Inspect original requirements, allowed changes, input/output examples, evaluator,
runtime/setup and submission contract together. Keep original files and tests.
In `run/FINALS_RUN.md`, record source locations, active rules/unknowns, protected
contracts, metric and direction/units, deliverables and real cutoff. Existing
preliminary run files may remain; do not relabel their approvals as finals review.

Explain the task in a few Korean sentences: who needs the result, input, required
output, what counts as success and one source-backed example. Choose a task lane
from the playbook; AI-assisted development does not require an AI runtime/model.
Do not preselect a chatbot, ML model, semiconductor scenario, UI or slide deck.

Observe the actual clock, record its timezone and confirm official cutoffs.
Estimate intake, first working output, improvement, checks/repair, packaging and
any confirmed explanation/pitch requirements. Replan after a material failure or
rule change; a percentage schedule is not an official rule. Preserve enough time
to produce, verify and collect a valid smaller result. Do not treat all 390 event
minutes as available or borrow time from an unconfirmed lunch/transition period.

## Build the first complete path

Inspect command side effects and data/network routes before execution. Use the
original task toolchain and minimum necessary permitted dependencies. Reuse the
baseline logic from the existing kit; do not invoke preliminary role/policy
procedures through a helper. Capture a bounded pre-edit check or the concrete
reason it cannot run. For a blank project, preserve a simple first solution as
the comparison baseline, explicitly labeled as such.

Review the proposed contract/approach against originals before product edits;
check substantive constraints and unknown permissions. An unresolved unknown
blocks only dependent work. A known official conflict is not an assumption.
Have clean CONSTRAINT_RED inspect that actual contract and DATA_EVAL_RED inspect
input/evaluator semantics before their numbers drive optimization or claims.
Then implement the smallest input-to-required-output path and actually run it.
Use provided examples and at least one relevant boundary/failure case when
available. Avoid scaffolding, polish and model training that do not serve scoring.
Keep temporary checks/data outside the actual collected deliverables.

At first complete output, report the observed result and execution evidence.
Test the task lane's consequential risk, then run separate ALGORITHM_RED,
CODE_RED and EDGE_RED at this first complete path when authorized/available,
under the rules above. Fix real defects before adding complexity. Do not count
file creation, a server starting, lint, or an internal note as an end-to-end pass.
Follow the actual launch/completion protocol. A new checkpoint needs a new clean
reviewer; a same-checkpoint reviewer may recheck its own findings. After ordinary
settings edits run cheap relevant regressions; material algorithm/objective,
evaluator/split or trust-boundary changes require affected clean review rather
than blindly refreshing receipt hashes.

## Improve against evidence

Choose the next change from the task metric, a reproduced error or a confirmed
requirement. Preserve the best verified valid version and baseline reports.
Use comparable data/split, evaluator, bounds and options for claimed improvement;
record source/version and exact results. Changed scope starts a separate series.
Never train/tune on held-out answers, weaken checks, invent official weights or
claim hidden score. If no metric is supplied, use small requirement-based checks
and call them local evidence. A sophisticated model that loses to the baseline
does not become the default just because the event mentions AI.

Stop repeated unproductive experiments within the actual time budget. Retain a
valid smaller result rather than ship a broken last-minute improvement. Reopen
affected design/review when a material official constraint or architecture changes;
do not restart intake after every edit. Keep evidence and explanation current.

## Verify, explain and prepare collection

Stop feature expansion in time for relevant final checks, repair and collection.
Verify the current output schema, hard constraints, sample/edge cases, reproducible
run path, required files and applicable performance/quality metric. Recheck after
any later behavior change. Separate PASS, FAIL, UNVERIFIED and NOT_APPLICABLE with
reasons; disclose unavailable UI checks. Do not declare READY with a known official
violation or missing required artifact. An allowed partial result must be labeled.

At the current final candidate, complete the six core final reviews and triggered
SECURITY_RED per finals-reviews.md. Sequence SUBMISSION_RED after other fixes so
it inspects the actual collected version/config/output, not an earlier directory.
Maintain run/FINALS_REVIEWS.json with common current required_scope hashes,
distinct worker IDs and verified findings. Run
`python .hackathon-kit/scripts/finals_review_check.py --checkpoint FINAL` using
the actual Python executable before claiming full independent quality review.
Missing/failed roles, stale configuration and unknown security activation fail
that claim. A known review gap may be honestly disclosed in an officially allowed
degraded/partial result; never waive an official prohibition or claim submitted.

Deliver a concise Korean explanation in chat, not only in notes: problem; actual
input-to-output flow; why this method; comparable baseline/current observations;
one actually observed rule-applied or boundary case; limits; exact run/demo and
submission steps. State missing baseline/case evidence rather than invent it.
Include the actual tools/algorithms and why they were chosen. For an optimizer,
identify a real solver, heuristic, enumeration or training optimizer correctly;
explain objective/constraints, relevant settings and observed termination/result.
Do not claim optimality from the tool name or certify participant comprehension.
Prepare a brief pitch or answers only if official requirements or the participant
request them; no mandatory six-question quiz or teach-back. Stop for any official
no-AI phase. Details and code may be linked without making the participant read
them to understand the result.

Run normal `kit_lifecycle.py doctor` for installation integrity when useful. It
uses preliminary STATE internally and does not validate finals readiness. Do not
use its `--pre-submit`, `gate_check.py`, or preliminary CLOSED/DONE values to claim
finals approval. Use the task-specific final checks and the finals run record.
Remove helpers only when required by the confirmed collection contract, after
preserving notes through the existing ownership-safe cleanup. Git ignore alone
does not exclude helpers from a folder/ZIP upload. Verify the actual collected
paths, required artifacts and size against that contract.

Distinguish VERIFIED LOCALLY, READY FOR HUMAN SUBMISSION, FROZEN and SUBMITTED.
Do not submit/publish/push without applicable authorization; do not claim receipt
from a prepared ZIP. The participant performs human-only UI actions with concise
instructions. Record the observed completion receipt if available, otherwise
submission remains UNVERIFIED. Never modify an already frozen submission.

## Resume after interruption

Read the finals run record, current files and retained evidence. Reconcile owned
workers and stop any previous writer before replacing it. Restore the last verified
candidate, next action, pending official question and deadline from evidence; do
not rescan private histories or restart the participant's explanation. Update only
the affected observations and keep preparation results separate from live results.
