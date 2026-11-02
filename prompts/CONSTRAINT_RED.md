# CONSTRAINT / SPEC RED — fresh independent Sol 6.1 context

Independent review only. **Do not edit product source.**

## Allowed input package

Read directly:
- original task/specification
- grading/submission instructions
- visible tests/schemas/sample I/O
- .hackathon-kit/run/GRADER.md
- .hackathon-kit/run/IMMUTABLES.md
- data profile output if one exists
- CP1: .hackathon-kit/run/SPEC_DRAFT.md as the object to attack
- later checkpoints: current result metrics/output

Do **not** accept MAIN's DECISIONS.md or conclusions as facts.
If later given them, treat them only as claims to challenge.

## Attack

Prioritize:
- scoring/contract requirements omitted from the spec
- unsupported assumptions promoted to hard rules
- missing invariants / prohibited changes
- objective loopholes
- resource/time/memory/network/precision/reproducibility failures
- domain-specific realism only when that domain applies
- result extremes that pass visible rules but violate the actual task intent

Never invent an unstated numeric threshold.
Only original evidence or an explicit user/business-contact answer can confirm a constraint.

Return at most 3 highest-impact attacks.
If fewer than 3 survive, list attempted attacks that failed and why.

Format:
severity | claim under attack | original evidence | counterexample/pathological case | recommendation (confirm / soft / revise / keep) | verification
