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

Have MAIN inspect original task/grading/submission sources, tests, schemas, samples, and runtime configuration once, then batch the findings into GRADER.md, BASELINE.md, IMMUTABLES.md, CONSTRAINTS.md, and SPEC_DRAFT.md. Apply `grader-intake → immutable-inventory → task-router → problem-intake → constraint-discovery` as reasoning steps over shared evidence, not repeated full repository scans.

For UI/chat-only instructions or unavailable original files, capture provenance-marked verbatim original/participant/Cofa excerpts in TASK_EVIDENCE.md. Distinguish excerpts from AI interpretation. Use this local record as a source path; do not invent an original source.

Inspect baseline command side effects and network use before execution. Bound checks using remaining exam time, expected runtime, and time needed for implementation, review, submission, and follow-up preparation. Record unavailable checks with reasons; never fabricate a passing baseline. Activate data/tool/domain playbooks only with task/grader evidence.

MAIN reports classification and intake outcomes; ORCHESTRATOR alone updates STATE. Ask the participant only material scoring/feasibility/business-rule questions. Otherwise record a reversible non-blocking ASSUMPTION and continue safely. No mandatory per-step interaction, teach-back, or manufactured human contribution.

# Clean review launch — every Red checkpoint

Create a new reviewer with no inherited conversation. Where supported, explicitly use `fork_turns="none"`; otherwise use a genuinely clean separate session. A new agent with full inherited history is not an independent review. If neither is available, keep the gate open and report the missing review; do not relabel an inherited review as independent.

Pass the role prompt, EXAM_POLICY.md, original task/grading/test/schema/sample paths, and only artifacts needed for that review. Read original sources first. All MAIN-authored documents, including GRADER/IMMUTABLES/SPEC and data profiles, are claims to verify, not independent authority. Do not include prior MAIN dialogue or DECISIONS as background facts. Record actual model and `NO_HISTORY` or `CLEAN_SESSION`; follow the same exam restrictions inside the isolated session.

# CP1 — SPEC FREEZE

Before product implementation, clean CONSTRAINT_RED attacks SPEC_DRAFT against original evidence. Return the highest-impact findings and attempted attacks; never hide an additional blocking defect to meet a reporting cap. ORCHESTRATOR persists the actual factual review as `run/CP1_RED.md` and the machine review receipt as `run/CP1_REVIEW.json`:

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

# CP3 — PRE-SUBMIT

Budget CP3 from estimated review/check/repair/submission/preparation time and the actual deadline; start earlier if needed. A 15–20-minute reminder does not guarantee that all remaining work fits. Stop feature expansion, then:

1. Clean final CODE_RED and CONSTRAINT_RED review the current result and original evidence; ORCHESTRATOR records findings and verified dispositions.
2. MAIN fixes submission-blocking defects and runs `verification`. P0/P1 cannot be waived at deadline; choose a valid smaller/partial solution if needed. Mark other unrun checks UNVERIFIED and state limitations honestly.
3. Recorder finalizes factual evidence notes. MAIN uses `final-explain` for factual explanation and `followup-prep` as the sole practice owner, covering all six official question slots. Do not quiz the participant twice or defer evidence collection to this checkpoint.
4. ORCHESTRATOR records cp3_code_red/cp3_constraint_red as DONE, verification as RECORDED, and followup_prep as DONE only after the corresponding work and six answer outlines are complete. Run doctor. Cleanup is last, after preparation and preservation of notes, and only if the submission format requires helper removal.

Use Cofa Helper for exam UI/submission questions and official incident reporting for repeated technical failures. The participant handles UI actions; no Computer Use/automated UI control, external task-data transmission, external AI connection, or Git Push.

# Context replacement and review budget

If MAIN's context degrades, have it send HANDOFF content to Recorder, stop the old writer, then start one replacement MAIN from evidence. If Recorder is unavailable, ORCHESTRATOR may explicitly transfer HANDOFF.md alone to MAIN for one sequential write, then return ownership. ORCHESTRATOR records the replacement; only one MAIN is active.

There are three planned checkpoints. Extra review is for material requirement/spec changes, a new blocking risk, major architecture change, or repeated failure; recheck affected findings/evidence rather than reopening every checklist after small edits.
