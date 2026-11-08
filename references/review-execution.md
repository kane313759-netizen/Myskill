# Observe review execution, not just dispatch

This protocol applies to actual CP1/Code/Constraint/Edge reviews in the selected
stage. It is a kit reliability rule, not an official exam rule or permission to
delegate. Keep current official rules and available capacity first.

The participant reported on 2026-11-08 that a second-preliminary CP1 subagent had
not run, discovered only after their own check. This is participant-reported
experience; no private session history was inspected and its technical cause is
unknown. Do not claim this maintenance change proves what happened historically.

## Observable lifecycle

The orchestrator owns this check; the nondeveloper must not have to discover a
missing worker. Use a new clean reviewer with its actual available tool API.

1. **REQUESTED:** prepare the scoped original sources, candidate and role. A prompt,
   dispatch intention or local report template is not a launched reviewer.
2. **LAUNCHED:** perform the actual launch and retain its returned worker/session ID
   and native response. A name written by the author is not an observed ID.
3. **RUNNING:** before relying on its review, observe that worker running through
   the tool's status surface or an actual worker acknowledgement tied to the ID.
   If a fast worker has already completed, its first actual response may establish
   that it ran; record that observation honestly, not an invented earlier heartbeat.
4. **COMPLETED:** receive the worker's final review or explicit completed status,
   verify its report exists and contains scoped findings/attempted attacks and
   executed-versus-static limits, and bind the reviewed candidate files. Dispatch
   return, an empty file or a parent's self-review cannot satisfy this step.
5. **ACCEPTED:** separately inspect the report, resolve blockers and recheck fixes.
   Execution completion alone is not review approval or a passing product.

Observe status soon after launch rather than first discovering a silent failure
at the final gate. Use bounded waits based on actual review budget; do not busy
poll. On launch failure/unknown ID, check for an already owned worker before retrying
to avoid duplicate writers/reviewers. On a stall, retain actual failure/pending
status, release other owned capacity or schedule sequentially, and report the gap.
Do not fabricate RUNNING/COMPLETE, replay another checkpoint's receipt, or ask the
participant to inspect agent controls as the normal path.

Missing tool support is a real limitation. Preliminary CP1 stays OPEN/NOT_RUN
without its actual independent review. Finals may continue independent permitted
work or perform a clearly labeled SELF_CHECK in degraded mode; tell the participant
which separate review is missing and never mark it independently reviewed. A
required official independent check still blocks the affected work/submission.

## Retained records and read-only validation

Retain relevant tool observations only, not private transcripts. Under the kit's
`run/reviews/<checkpoint-role>/`, keep three observation JSON files. Each contains
`worker_id`, `phase` (`LAUNCHED`, `RUNNING`, `COMPLETED`), timezone-aware `observed_at`,
`tool` and the actual returned `raw` object identifying that worker. Preserve
the original response; the wrapper's phase is the orchestrator's interpretation,
not an authenticated platform assertion. For fast completion, RUNNING and
COMPLETED may retain the same real response in separate phase records at the same
observed time; explicitly explain this, without inventing a prior running state.

Supported response shapes: a `collaboration.spawn_agent` return containing its
exact `task_name` establishes LAUNCHED only; a matching `collaboration.list_agents`
row (or its full `agents` list) carries `agent_name` and `agent_status`. Generic
structured tool responses can use exact `worker_id`/`task_name`/`agent_name`/
`agent_id`/`session_id` plus `status`, `state` or `agent_status`. Conflicting IDs or
statuses fail. A runtime final notification may be retained as its actual
`task_name`, `message_type: FINAL_ANSWER` and verbatim `text`; identify the worker
from the actual sender, not the recipient. Free text/incidental ID mentions and
unknown native shapes remain UNVERIFIED until a reviewed adapter is available.
Do not rewrite an unsupported response into an invented supported status.

Queued/pending/accepted establishes only launch; running/acknowledged establishes
activity; completed establishes completion (including a genuine fast completion).
Explicit failed/cancelled/not-run responses cannot be wrapped as successful
activity or completion. Duplicate JSON fields are rejected instead of last-wins.

Copy `templates/REVIEW_EXECUTION.json` for each review, fill actual IDs/context and
the three path/SHA256 pairs, actual report path/SHA256 and `reviewed_files` mapping
task-relative current code/spec paths to SHA256. Use a precise read set. Freeze
that receipt until a real targeted recheck is observed; never just refresh hashes.
Do not reuse another role/checkpoint/worker's observations. Product writer and
independent reviewer must be different workers; verify this in actual tool state.
Record actual models only when observable, otherwise explicitly UNKNOWN.

Run using the actual installed Python executable:

```text
python .hackathon-kit/scripts/review_execution.py --receipt .hackathon-kit/run/reviews/CP2-EDGE_RED/execution.json --role EDGE_RED --checkpoint CP2
```

The agent executes this command; the participant need not memorize it. All receipt
paths are relative to the task root. Observations/reports must stay under the
kit's run directory; reviewed source paths stay within the task root. Symlink,
missing, changed or oversized evidence fails rather than silently passing.

The checker validates retained lifecycle records, matching IDs, chronology and
current hashes. It cannot authenticate tool responses, prove model/context
isolation or prevent an author from inventing records. The orchestrator must
actually observe the tool responses. This improves detection of missing execution;
it does not make a mathematical guarantee that a subagent will always run.

CP1_REVIEW.json includes this object as `execution`; `gate_check.py` requires it
for the actual CONSTRAINT_RED CP1 report and five reviewed artifacts. Old receipts
without execution evidence fail closed; do not retrofit history. Existing run
notes are preserved on upgrade. Rerun a required current review when permitted,
or keep the gate open and explain what is missing. Finals and later preliminary
reviews use separate receipts; the helper is not a finals readiness checker.
