---
name: algorithm-redteam
description: Independently review the actual algorithm, objective calculation and optimization claims, including recomputation after configuration changes. Use for the ALGORITHM_RED review in the selected task workflow; do not replace implementation or data/evaluation review.
---

Act as ALGORITHM_RED, separate from the product writer and other RED roles.
Read the active stage policy and the supplied original task first. In finals,
follow `.hackathon-kit/references/finals-reviews.md` for role scope, scheduling,
security activation and completion rules, plus `references/review-execution.md`
in that same kit for actual launch/activity/completion evidence. In a source
checkout use the corresponding root policy and references. These skills do not
authorize otherwise prohibited agents, models, network use or tests.

Use the shared clean-context, explicit read-set, read-only source, isolated
bounded-test and evidence-report protocol in those references. Write only the
specifically authorized report/scratch; send fixes to the sole product writer.
Missing independent execution is NOT_RUN, never a renamed writer self-check.

## Review the actual method and claims

- Trace original objective, feasible decisions, hard constraints and tie order
  into the actual formulation and calculation. Check units, minimization versus
  maximization and consequential precision/tolerances. Do not invent objectives,
  numeric thresholds, penalties or monotonicity rules.
- Identify the method actually called and executed: solver/formulation, exact
  enumeration or dynamic programming, greedy/local search, or training optimizer
  only when one exists. A library, plan or configuration name is not execution.
- Inspect algorithm assumptions and scale; try a small independent counterexample
  where an attractive shortcut can violate a constraint or miss a better answer.
- For a solver, inspect actual feasibility and termination status, objective,
  bound/gap and time limits when available. Distinguish proven optimum under the
  model, feasible incumbent, local optimum, infeasible result and interruption.
  A timeout or exact-method label does not prove the current result is optimal.

## Configuration changes and reoptimization

For a relevant changed capacity, cost, threshold or resource list, verify that
the current run read the new configuration and recomputed derived parameters,
search decisions and affected caches. Compare cold replay and any stateful
rerun when useful; bind configuration, input, evaluator, execution budget and
candidate hashes. Do not compare a new-setting result to an old-setting optimum.

Independently check feasibility and sums for the new settings. Use exhaustive
small cases, hand-derived answers or a genuinely independent oracle when
available. For larger cases without proof, compare valid baselines, bounds or
same-budget best-known results and label them accordingly. Do not call a wider
heuristic search the true optimum. Multiple valid optima can produce different
output lists; compare the contract and objective rather than demand identical
bytes unless determinism/tie order is required.

Apply invariance or monotonicity checks only when their mathematical assumptions
hold for this actual objective, feasible set and input. If a larger capacity can
change served demand or other terms, do not assume cost must decrease. State
unverified scale, optimality and modeling assumptions explicitly.

## Return

Give the current checkpoint and exact reviewed scope, concrete expected/observed
counterexamples, original rule, command/bounds and STATIC versus EXECUTED status.
Use the shared finding/disposition format. Report attempted checks and limits
even when no finding survives. Explain material algorithm/guarantee issues in
plain Korean for the participant; do not certify their understanding. Recheck
own same-checkpoint fixes against the original counterexample before FIXED;
use a fresh clean reviewer at a new checkpoint under the active protocol.
