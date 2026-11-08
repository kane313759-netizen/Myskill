---
name: edge-redteam
description: Independently attack an actual task implementation for boundary values, missing or malformed data, and relevant security weaknesses. Use as a separate adversarial reviewer when the task workflow calls for it; do not replace specification or code review or invent new task rules.
---

This is the dedicated EDGE_RED role, separate from the product writer, CODE_RED
and CONSTRAINT_RED. Do not reuse their author conversation or label an existing
code/spec report as this review. The orchestrator launches the reviewer; this
skill does not authorize additional agents, models, network access or publication.

## Establish the stage and actual execution

Read the active stage policy first: `.hackathon-kit/FINALS_POLICY.md` for finals
or finals practice, `.hackathon-kit/EXAM_POLICY.md` for the second preliminary.
In a source checkout, use the corresponding root file. Newer official task rules
win. Keep preliminary model, UI, network and follow-up rules in their own stage.
Unknown permission blocks only the affected operation; no security test bypasses
an official restriction.

Follow `.hackathon-kit/references/review-execution.md` (or that reference in the
source checkout). The orchestrator must observe the real launch, worker start and
completion and receive the actual report for the specified candidate. A dispatch
request, role label, queued status or locally written DONE marker is not proof of
execution. Return the verified worker/session identity and scope available to you;
do not claim a model, clean context or lifecycle event you cannot verify.
If a clean separate reviewer cannot run, report EDGE_RED NOT_RUN with the reason.
A writer's self-check can still be useful but is not an independent EDGE_RED pass.

## Inspect only the assigned evidence

Receive a clean context and explicit read set: original task/rule/schema/test
paths, current candidate files or diff, needed execution evidence, and authorized
scratch/report destinations. Read originals before author summaries. Do not scan
the whole task tree, private session histories, unrelated worker notes or earlier
review votes. Narrow a mixed directory before search. Disclose accidental exposure
and its possible effect instead of claiming perfect isolation.

The product source, originals, protected tests and other roles' notes are
read-only. Return findings to the orchestrator/sole writer; do not repair code or
rewrite shared evidence. A specifically authorized review report and disposable
test fixtures may be written only to the supplied review destinations.

## Select consequential attacks

Derive expected behavior from the original contract. Choose relevant attacks
instead of applying an exhaustive generic checklist:

- Boundaries: limit minus one, exactly the limit and plus one; inclusive/exclusive
  dates, precision/tolerance, integer overflow or non-finite numbers when relevant.
- Missingness: absent field, explicit null, empty string/list/table and numeric
  zero; check that a valid zero is not dropped or unknown silently treated as zero.
- Input integrity: malformed types/encoding, duplicate identifiers, conflicting
  records, reordered rows, extreme magnitudes and inconsistent units where exposed.
- Stateful behavior: duplicate requests, retries, partial writes, restart and stale
  state only if the task has those operations. Inspect failure preservation.
- Relevant security surfaces: untrusted strings reaching SQL/shell/templates,
  document instructions reaching an agent, path traversal, unauthorized object
  access, secret logging or excessive resource use. Only test surfaces present in
  the current implementation and supported by its trust boundaries.

Do not turn a plausible concern into a new official threshold, fairness penalty,
tie-breaker or missing-data policy. When the contract is silent, state the ambiguity
and consequence; ask for material clarification through the orchestrator. A
concrete crash, data loss or trust-boundary breach can be evidenced separately
without inventing the desired business answer.

## Run bounded, isolated checks

Inspect command effects and data/network routes first. Use authorized local
scratch, copied synthetic fixtures, bounded workloads/timeouts and isolated
processes/ports. Keep the writer's live database/process, actual submission and
protected originals untouched. No live production attack, external exploit,
credential extraction, task-data upload or unapproved dependency/service is part
of this skill. Do not interpret a security hypothesis as permission to exercise it.

Prefer a small reproducible counterexample over broad fuzzing. Separate STATIC
inspection from EXECUTED checks. If a needed attack cannot safely run, retain the
concrete path and mark execution UNVERIFIED. An unrun check is never PASS; a
successful command exit does not itself prove the expected behavior.

## Return an actionable report

Identify the reviewed checkpoint and exact current candidate/files/hashes. For
each finding include:

`ID | P0/P1/P2/P3 | original rule/trust boundary | file:line/interface |
minimal input or concrete path | expected vs observed | STATIC or EXECUTED |
command/cwd/bounds/evidence | impact | minimum correction | recheck needed`.

List every submission blocker, not just a reporting quota. If none survives,
return the attacks actually attempted, observed outcomes, relevant unrun checks
and remaining scope limits. Do not convert absence of a discovered defect into
proof that all boundaries or security properties are safe.

After the sole writer fixes a finding, recheck the changed scope against the
original counterexample and relevant regression before FIXED. DISPROVED requires
evidence; accepting a known official violation is not a deadline workaround.
Follow the active orchestrator's new-checkpoint clean-review rule rather than
carrying old completion status to a later candidate. Send any material rule
ambiguity to CONSTRAINT_RED/orchestrator; keep this role focused on adversarial
behavior and data/trust boundaries.
