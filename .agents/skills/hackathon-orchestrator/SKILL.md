---
name: hackathon-orchestrator
description: Orchestrate the SK hynix exam through one MAIN, evidence-backed gates, independent reviews, and the official six-question follow-up preparation.
---

Read `.hackathon-kit/EXAM_POLICY.md` first. Official exam/task instructions always win.
This file is the canonical checkpoint and role protocol; role prompts specialize it without adding checkpoints.

# Ownership

- ORCHESTRATOR: Terra 5.6 when available. Dispatches agents; exclusively writes STATE.md, checkpoint reports, CP1_REVIEW.json, and gate state. No product-source edits.
- MAIN_BUILDER: one persistent Sol 6.1 when available. Sole product-source writer. Authors Phase 0 intake/spec artifacts; sends later evidence and handoff content to Recorder. Never writes STATE/gate/checkpoint records.
- CODE_RED: clean Terra context. Returns review evidence; no product-source or shared-note edits.
- CONSTRAINT_RED: clean independent Sol 6.1 context. Returns spec/constraint review evidence; no product-source or shared-note edits.
- RECORDER: Luna 6 when available. Sole ongoing evidence-note writer under `.hackathon-kit/run/`. Never writes STATE, checkpoint reports, CP1_REVIEW.json, or frozen intake artifacts; no product-source edits.
- TUTOR: optional Sol 6.1 session, strictly read-only. The participant may forward an explicitly confirmed personal judgment/check to MAIN or Recorder; Tutor must not infer participant actions or write notes.

Verify actual available models and record actual selections. Keep these preferred models; if unavailable, use the strongest allowed available substitute with the same role boundaries. Do not claim an unverified model switch.

# Phase 0 — one evidence pass

Have MAIN inspect original task/grading/submission sources, tests, schemas, samples, and runtime configuration once, then batch the findings into GRADER.md, BASELINE.md, IMMUTABLES.md, CONSTRAINTS.md, and SPEC_DRAFT.md. Use the installed run/templates in place and preserve their level-2 section headings; the gate checks these sections. MAIN runs `python .hackathon-kit/scripts/gate_check.py --preflight` before Red dispatch so document-format corrections happen before an independent review. A preflight pass never authorizes implementation or substitutes for the full gate. Apply `grader-intake → immutable-inventory → task-router → problem-intake → constraint-discovery` as reasoning steps over shared evidence, not repeated full repository scans.

For UI/chat-only instructions or unavailable original files, capture provenance-marked verbatim original/participant/Cofa excerpts in TASK_EVIDENCE.md. Distinguish excerpts from AI interpretation. Use this local record as a source path; do not invent an original source.

Inspect baseline command side effects and network use before execution. Bound checks using remaining exam time, expected runtime, and time needed for implementation, review, submission, and follow-up preparation. Record unavailable checks with reasons; never fabricate a passing baseline. Activate data/tool/domain playbooks only with task/grader evidence.

Make progress measurable using `.hackathon-kit/references/local-evaluation.md` in this same intake
pass. Prefer supplied visible grading; otherwise use only small useful local checks
from original requirements. Bind local rubric/checker/oracle hashes in the existing
GRADER or SPEC and preserve the pre-edit report/version/scope in BASELINE. CP1 Red
reviews these as claims, including relevant positive/negative controls. No new role,
checkpoint, gate bit or required numerical target is added. Official native metrics
and local declared-check coverage remain separate; unknown weights stay unknown.

Keep normal routing on original task tools, kit helpers and the standard library;
optional additions are NONE. Do not automatically inventory, adopt or install catalog
helpers, even if already present. Preserve permitted original project setup and
genuinely necessary product dependencies for a new task; convenience alone does not
make an optional helper required. MAIN records original evidence, required setup,
fallback, guards and budget in the existing SPEC verification plan for CP1. Missing
required work remains blocked/partial. The optional catalog is for separate preparation
or a new specific request, not a routine search or participant-approval loop.

MAIN reports classification and intake outcomes; ORCHESTRATOR alone updates STATE. Ask the participant only material scoring/feasibility/business-rule questions. Otherwise record a reversible non-blocking ASSUMPTION and continue safely. No mandatory per-step interaction, teach-back, or manufactured human contribution.

# Clean review launch — every Red checkpoint

Create a new reviewer with no inherited conversation. Where supported, explicitly use `fork_turns="none"`; otherwise use a genuinely clean separate session. A new agent with full inherited history is not an independent review. If neither is available, keep the gate open and report the missing review; do not relabel an inherited review as independent.

Pass the role prompt, EXAM_POLICY.md, original task/grading/test/schema/sample paths, and only artifacts needed for that review. Read original sources first. All MAIN-authored documents, including GRADER/IMMUTABLES/SPEC and data profiles, are claims to verify, not independent authority. Do not include prior MAIN dialogue or DECISIONS as background facts. Record actual model and `NO_HISTORY` or `CLEAN_SESSION`; follow the same exam restrictions inside the isolated session.

Supply an explicit read set: original source paths, current product roots and
specifically shared evidence files. Reviewers must scope search/list commands to
these paths; do not discover the whole task tree or enumerate other roles' scratch,
notes or outputs. Narrow any mixed directory before searching it. Report accidental
exposure, what was seen and its possible effect; do not claim perfect isolation.
Assess whether a fresh clean review is needed for a material exposure.

Private agent histories, session logs and harness output stores (including those
under `~/.claude` and `~/.codex`) are outside the review read set. ORCHESTRATOR may
share specific task-evidence reports, but cannot waive isolation by authorizing
another role's private scratch or history.

Before using a role's scratch path as cwd/TMPDIR, create its own directory from a
known existing authorized parent. Use the installed prompt paths and current
documented command syntax; inspect help on an argument error instead of guessing.
If agent capacity is exhausted, retain the original request, finish/release owned
auxiliary work and schedule required reviews sequentially. An existing Red may only
recheck its own findings within the same checkpoint; it cannot supply the independent
review for a new checkpoint. A new checkpoint, including CP3, must wait for a new
NO_HISTORY/CLEAN_SESSION reviewer under the launch rule above. While waiting, keep
that checkpoint's review status NOT_RUN; never copy an earlier DONE or relabel an
old session as clean. Reuse other existing roles only for work consistent with their
ownership and history. Relay a question only through an already
authorized participant/support channel, without changing its content. Do not invent
an answer or introduce external AI/UI automation. Missing independent review keeps
the relevant gate open; an unavailable tool is not a passing check.

# CP1 — SPEC FREEZE

Before product implementation, clean CONSTRAINT_RED attacks SPEC_DRAFT against original evidence. Return the highest-impact findings and attempted attacks; never hide an additional blocking defect to meet a reporting cap. ORCHESTRATOR persists the actual factual review as `.hackathon-kit/run/CP1_RED.md` and the machine review receipt as `.hackathon-kit/run/CP1_REVIEW.json`:

- `version: 1`; `status: COMPLETE`; `reviewer: {role: CONSTRAINT_RED, actual_model: <verified model>, context_mode: NO_HISTORY | CLEAN_SESSION}`
- `source_paths`: nonempty original task/grading/test evidence paths, or provenance-marked TASK_EVIDENCE.md when originals are unavailable
- `artifacts`: SHA-256 of the exact reviewed GRADER.md, BASELINE.md, IMMUTABLES.md, SPEC_DRAFT.md, and CONSTRAINTS.md
- `findings`: `{id, severity: P0|P1|P2|P3, status: OPEN|FIXED|DISPROVED|ACCEPTED_RISK, evidence, verification}`
- `attempted_attacks`: evidence-backed descriptions of attacks attempted, including when no finding survives

Resolve every P0/P1 finding: FIXED requires verification of the fix; DISPROVED requires original evidence and verification. OPEN or ACCEPTED_RISK P0/P1 cannot close the gate. Official-rule or submission-blocking conflicts are blockers regardless of a convenient label. Non-blocking accepted risks remain explicit in LIMITATIONS. Only original evidence or an explicit participant/business-contact answer can confirm a constraint.

Use `python .hackathon-kit/scripts/gate_check.py --artifact-hashes` to obtain the current five hashes; this utility does not approve or close the gate. The receipt hashes must describe what Red actually reviewed. After a fix, obtain a targeted reviewer recheck before updating reviewed hashes/dispositions; do not merely rehash new files to make stale approval pass.

Once intake evidence, the actual CP1 review, and dispositions are complete, ORCHESTRATOR records the canonical STATE fields and candidate CLOSED state, then runs:
`python .hackathon-kit/scripts/gate_check.py`

The checker is read-only; CP1_REVIEW.json is the review receipt. Only a successful check against current artifacts authorizes product implementation. On failure, restore OPEN and resolve the reported evidence gap. MAIN verifies the gate before its first product edit. The checker validates structure, hashes, and dispositions; it cannot prove actual model/context isolation or the truth of business claims. ORCHESTRATOR must verify those independently.

Freeze GRADER, BASELINE, IMMUTABLES, SPEC_DRAFT, and CONSTRAINTS after approval. Put routine results in VERIFY/DECISIONS/LIMITATIONS rather than rewriting these artifacts. Material task/spec/constraint changes reopen the gate and require a targeted clean Constraint Red recheck with updated artifacts/hashes before continuing affected implementation. Any unexpected hash mismatch requires investigation, not automatic receipt refresh.

# Build and CP2 — FIRST END-TO-END

MAIN builds the smallest scoring-relevant end-to-end path. Preserve contracts/tests; never hard-code samples or replace the submission wholesale with external code. Partial reuse must respect the official brief and task rules.

At the first working scoring-relevant path, run clean CODE_RED and then Recorder. Repeat Constraint Red only for a material assumption/constraint/objective risk. Inspect dynamic-test side effects; isolate temporary data, processes, and ports, and avoid MAIN's live DB/process. Report necessary checks that cannot safely run as UNVERIFIED. MAIN sends factual evidence to Recorder, which maintains ongoing notes and prepares six-axis follow-up coverage early.

Recorder retains baseline/CP2/final local coverage under unchanged rubric, evaluator
hashes and known input/policy/options scope. Cheap affected checks may track material
progress between checkpoints; heavy reruns need a relevant change/failure/contract.
Changed checks/scope are non-comparable, never silent score improvement. A local
maximum does not replace the original tests, independent reviews or official rules.

Reuse the reviewed task toolchain after routine edits; do not add optional helper
experiments. MAIN sends actual errors/results to Recorder. Material dependency,
mutation or network/data-route changes use the normal reopen/review rule before
affected work; ordinary setup/use already reviewed does not itself reopen CP1.
At CP3 keep helper reports/caches outside the collected submission. PATH presence,
lint success or empty extraction is not product verification.

# CP3 — PRE-SUBMIT

Record the official exam clock/timezone and the earlier of the stage cutoff and whole-exam cutoff. The latest confirmed official schedule is 2026-11-04 19:00–23:00 as printed in the guide; confirm the official timezone in the exam UI and do not reuse that date for a future exam. Newer official UI instructions always win. The guide describes about 5 minutes of question-generation transition (excluded from solving but included in the total window); the UI may show up to 10 minutes per attempt and restart preparation on automatic retry. Late starts, waiting and retries do not extend 23:00. Reserve the full 30 minutes for six follow-up answers and transition time when planning the latest solving submission, and start submission at least 10 minutes before that deadline as the detailed guide recommends. Never infer exam time from the host UTC clock alone.

Current-time/remaining-time reports need an actual clock-tool or system-clock
observation and the officially confirmed deadline/timezone. Never guess the current
time or hard-code a retest date. A host clock observation does not establish the
official exam schedule. If either source is unavailable, state UNKNOWN and obtain
the missing official time through the participant/Cofa channel.

Budget CP3 from estimated review/check/repair/submission/preparation time and the actual deadline; start earlier if needed. A 15–20-minute reminder does not guarantee that all remaining work fits. Stop feature expansion, then:

At the reserved submission-start boundary (at least 10 minutes before the planned
solving cutoff), notify the participant to manually open "제출하고 문제풀기".
Do not delay this notification behind Recorder updates, doctor or optional rehearsal.
Preview is not confirmation: close it to make still-permitted fixes, check required
files/collection scope, saved state and the 10GB total, and resolve submission blockers
or use a verified valid partial result. Finish the essential factual explanation and
six outlines within the remaining time; report omissions rather than invent completion.
The participant manually chooses "제출물 확정하고 문제풀기"; this freezes files.
After question preparation, the participant starts the questions, answers without AI
or paste, and checks final completion plus submission ID/time/file count/size.
No automated UI action or post-confirmation file/record update is permitted.

1. Clean final CODE_RED and CONSTRAINT_RED review the current result and original evidence; ORCHESTRATOR records findings and verified dispositions.
2. MAIN fixes submission-blocking defects and runs `verification`. P0/P1 cannot be waived at deadline; choose a valid smaller/partial solution if needed. Mark other unrun checks UNVERIFIED and state limitations honestly.
   Before collection/freeze, any later behavior-changing edit needs affected Code
   Red review under the launch/reuse rules above and relevant verification within
   the existing checkpoint. Reconcile changed
   product and required runnable-document paths with the last reviewed version in
   the existing checkpoint report/VERIFY before READY. A text-only edit still needs
   source/command consistency checks; equal result bytes do not prove code safety
   or permit any edit after actual collection/freeze.
3. Recorder finalizes factual evidence notes. MAIN uses `final-explain` for factual explanation and `followup-prep` as the sole practice owner, covering all six official question slots. Do not quiz the participant twice or defer evidence collection to this checkpoint.
4. Before declaring preparation complete, ORCHESTRATOR reads the final VERIFY/LIMITATIONS/FOLLOWUP_CHEATSHEET against the latest checkpoint dispositions and current code version. If a late clarification, review decision, or fix occurred after Recorder prepared the notes, send the actual new evidence back to Recorder and refresh only affected claims/outlines; do not repeat a whole quiz. A resolved finding must not remain pending in the final answer sheet, and earlier reproduced failures must not be erased.
   During the permitted preparation phase, deliver the concise final explanation and six prepared outlines to the participant. Check the actual delivered coverage against current evidence; internal notes or an agent return alone do not establish delivery. Record any time-limited omission honestly, preserve the submission deadline, and do not restart completed practice. This adds no per-step teach-back or second quiz.
   Confirm that the delivered text contains the actual before/current observations
   and one real rule-applied case required by `final-explain`, or their explicit
   evidence gap/reason. Do not ask the participant to discover these missing facts.
5. Before marking either CP3 Red DONE, ORCHESTRATOR checks its existing checkpoint
   report for the actual fresh reviewer/session, creation method and
   NO_HISTORY/CLEAN_SESSION mode, current reviewed code/result scope, findings and
   dispositions. An earlier checkpoint's review or its targeted fix recheck cannot
   satisfy this final review. A context label alone does not establish a fresh
   launch; report missing evidence and leave that review NOT_RUN rather than DONE.
   Record cp3_code_red/cp3_constraint_red as DONE, verification as RECORDED, and
   followup_prep as DONE only after the corresponding work and six answer outlines
   are complete. Run doctor. Cleanup is last, after preparation and preservation of
   notes, and only if the submission format requires helper removal.

Before declaring writer stop/READY, finish factual completion updates using already
observed results. Notes and answer outlines never delay READY or collection. After
READY, Recorder may finish affected notes only when GRADER shows they are not
collected, and only before any required cleanup and confirmation/freeze; anything
unfinished or undelivered (step 4) is reported as pending. Distinguish ready for
collection from actual collection/freeze.
After a stop/freeze instruction, report any pending record rather than silently
marking it complete or resuming writes; only an explicit authorized pre-freeze
resumption may finish it. A frozen submission is never rewritten for a later grade.

When a material official change arrives before freeze, after CP3 or near the
deadline, observe the clock and record the latest READY time (the planned solving
cutoff minus the reserved submission time). Keep the gate order: a targeted Constraint Red
recheck of the changed scope only. Data checks, test preparation and review of
unchanged parts may run in parallel; related product edits start only after the gate
re-closes, then affected verification and Code Red. Product edits change collected
files, so tell the participant whether the workspace is the last reviewed version or
an unreviewed partial change. Update only changed facts in notes and outlines; the
submission-preview notification above still fires at its reserved time. If this path
cannot finish by the latest READY, tell the participant immediately with the observed
times and remaining steps and route deadline questions through the participant/Cofa
channel. Do not invent an exception, relabel or reuse reviews, or mark unfinished work
DONE; report the actual gate/review status.

Use Cofa Helper for exam UI/submission questions and official incident reporting for repeated technical failures. The participant handles UI actions; no Computer Use/automated UI control, external task-data transmission, external AI connection, or Git Push.

# Context replacement and review budget

If MAIN's context degrades, have it send HANDOFF content to Recorder, stop the old writer, then start one replacement MAIN from evidence. If Recorder is unavailable, ORCHESTRATOR may explicitly transfer HANDOFF.md alone to MAIN for one sequential write, then return ownership. ORCHESTRATOR records the replacement; only one MAIN is active.

After interruption/reconnect, reconcile known owned sessions, outstanding requests,
pending reports and authorized file changes before dispatching a replacement. An
unknown worker status is not completion; confirm the old writer has stopped before
starting another. Use explicit shared evidence, not private session-log discovery.

There are three planned checkpoints. Extra review is for material requirement/spec changes, a new blocking risk, major architecture change, or repeated failure; recheck affected findings/evidence rather than reopening every checklist after small edits.
