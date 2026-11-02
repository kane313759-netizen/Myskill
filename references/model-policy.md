# Model role policy — FINAL

## ORCHESTRATOR — Terra 5.6

Owns:
- workflow state
- checkpoint timing
- subagent dispatch
- findings aggregation

Does **not** own normal implementation.

## MAIN BUILDER — Sol 6.1

Owns:
- problem understanding
- requirements/specification
- architecture and system boundaries
- implementation
- integration
- difficult debugging
- final explanation

Keep the same MAIN context/worker when possible.

## CODE RED — Terra 5.6

Independent review only:
- implementation bugs
- boundary values
- missing/duplicate data paths
- persistence and retry
- regression
- bad tests

No source edits.

## CONSTRAINT RED — independent Sol 6.1

Independent problem-definition review:
- explicit constraint gaps
- implicit reality constraints
- unlimited-resource loopholes
- human burden
- fairness
- trade-offs
- extreme values
- objective-function exploits

No source edits. Treat MAIN assumptions as hypotheses, not facts.

## RECORDER — Luna 6

Records only:
- input/process/storage/output/external map
- constraints
- decisions
- verification evidence
- unresolved risks
- follow-up explanation points

## Mental model

> Sol builds. Terra breaks the code. Another Sol breaks the problem definition. Luna records.
