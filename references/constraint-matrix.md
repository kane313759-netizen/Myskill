# Constraint discovery matrix

Start with **grading/contract constraints**, then apply only relevant domain lenses.

| Common dimension | Questions |
|---|---|
| Grading / submission | What is scored? Which output/path/command is required? Hidden-test contract? |
| Immutable contract | Which API/schema/file/test/interface must remain compatible? |
| Input/output | Exact format, ordering, encoding, tolerance, malformed input behavior |
| Runtime | time, memory, CPU/GPU, network availability, dependencies |
| State | persistence, restart, stale state, sessions |
| Retry / duplicate | idempotency, partial failure, duplicate side effects |
| Reproducibility | seed, time, timezone, nondeterminism |
| Security/privacy | secrets, PII, authorization, leakage |
| Scale | real input size vs sample size |
| Failure / scoring | hard failure, partial credit, fallback behavior |

## Conditional domain lenses

Optimization/operations only:
resource/cost/capacity/utilization/unassigned/wait/travel/fairness/extremes.

Web/API/automation only:
latency/timeout/rate limit/retry/idempotency/auth/persistence.

Data/ML only:
missingness/leakage/split/metric/seed/class balance/baseline.

Algorithm/parser only:
complexity/exact I/O/determinism/precision/tolerance/malformed cases.

Always distinguish:
- CONFIRMED — evidence or explicit answer
- ASSUMPTION — plausible but unconfirmed
- OPEN QUESTION — material unknown
- NOT_APPLICABLE

Never invent a numeric threshold because it seems reasonable.
