# Model role policy — exam-specific

The official brief recommends Sol 6.1, Terra 5.6, Luna 6, and Sol 6.0. Verify actual availability and selection in the provided Codex environment. EXAM_POLICY.md remains authoritative; no external AI connection or restricted model may be introduced as a fallback.

The canonical role/checkpoint protocol is `hackathon-orchestrator`. Preferred assignments remain:

| Role | Preferred model | Ownership |
|---|---|---|
| ORCHESTRATOR | Terra 5.6 | Agent dispatch; exclusive STATE/checkpoint/gate records; no product edits |
| MAIN_BUILDER | Sol 6.1 | One active product-source writer; Phase 0 intake/spec; implementation/fixes/explanation |
| CODE_RED | Terra 5.6, clean context | Independent implementation/contract/regression review; returns evidence only |
| CONSTRAINT_RED | Sol 6.1, clean context | Independent spec/objective/constraint review; returns evidence only |
| RECORDER | Luna 6 | Sole ongoing evidence-note writer; no STATE/checkpoint/receipt/frozen-artifact edits |
| TUTOR | Sol 6.1, optional | Strictly read-only explanation; no inferred participant judgments or file writes |

Use the preferred available model; do not downgrade merely to shorten the workflow. If unavailable, preserve role boundaries, use the strongest allowed available substitute appropriate to the role, and record verified actual selection. Never claim a model switch without checking it.

Each Red review starts without inherited MAIN history: explicitly `fork_turns="none"` where supported, otherwise a genuinely clean session. Pass EXAM_POLICY and original task evidence first; treat MAIN-authored artifacts as claims. Record actual model/context, recognizing that a machine receipt cannot prove those runtime facts.

Review priority remains task-dependent: optimization/operations emphasizes Constraint Red; debugging/web/API emphasizes Code Red; algorithm/parser emphasizes exact contracts/hidden-test behavior; ML emphasizes metrics/leakage/reproducibility. CP1 and CP3 remain independent reviews for every task type. Changing model assignments is not a substitute for fixing blockers or completing six-question follow-up preparation.
