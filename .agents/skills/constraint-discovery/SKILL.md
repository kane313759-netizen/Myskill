---
name: constraint-discovery
description: Build an evidence-backed constraint register for an unfamiliar task; use before implementation and again only when a material requirement or result risk changes.
---

Read:
- `.hackathon-kit/EXAM_POLICY.md`
- `.hackathon-kit/run/GRADER.md`
- `.hackathon-kit/run/IMMUTABLES.md`
when present.

# Common constraints first

Inspect original task material, tests, schemas, sample I/O, runtime config, and submission rules for:
- input/output contract
- allowed/forbidden changes
- time and memory
- network/external dependencies
- state/persistence/retry/duplicate behavior
- reproducibility/seed/timezone/tolerance/encoding
- security/privacy/auth boundaries when relevant
- failure/partial-credit conditions
- performance/scale requirements
- explicit domain limits

Every CONFIRMED constraint needs an evidence path/location or explicit user/business-contact answer.
Without evidence, label it ASSUMPTION or OPEN QUESTION.

# Domain lenses are conditional

Only after task-router classifies the task, apply relevant lenses:
- optimization/operations: resources, capacity, utilization, unassigned items, wait/travel/fairness/extremes
- web/API/automation: contract, latency/timeout, retries, idempotency, persistence, authorization
- data/ML: leakage, split/seed, missing data, class balance, metric definition
- algorithm/CLI/parser: exact I/O, determinism, complexity, tolerance, malformed input

Do not leak optimization vocabulary into unrelated tasks.

# Extreme-value attack

For the relevant domain ask:
- what can be increased without limit to game the score?
- what can approach zero and create a pathological result?
- can a summary metric hide a catastrophic worst case?
- can visible samples pass while the contract is violated?

Write/update `.hackathon-kit/run/CONSTRAINTS.md`.
A MAIN may propose, but only evidence/user answer may promote ASSUMPTION → CONFIRMED.
