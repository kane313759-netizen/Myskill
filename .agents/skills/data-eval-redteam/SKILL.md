---
name: data-eval-redteam
description: Independently review task data and evaluation validity, including joins, units, leakage, split separation and an internally written grader. Use for DATA_EVAL_RED when the workflow requests this review; do not infer business truth or hidden scores from a passing local metric.
---

Act as DATA_EVAL_RED, separate from the product writer and other RED roles.
Read the active stage policy and original task/metric/data-definition evidence
first. In finals follow `.hackathon-kit/references/finals-reviews.md` for role
scope, scheduling and completion, and `references/review-execution.md` in that
kit for actual launch/activity/completion evidence. Source checkouts use their
root policy/references. Review cannot authorize prohibited tools or data routes.

Use the shared clean-context, scoped read-only source, bounded isolated-check
and report protocol. Do not inspect private histories, other review votes or
unassigned files. Write only assigned scratch/report; the product writer fixes.
Unavailable independent review stays NOT_RUN, not a relabeled self-check.

## Data validity for the actual task

- Inspect relevant key meanings, cardinalities and join row counts, duplicates,
  units/scales, timezones and effective definition/version dates. Trace a real
  small record through consequential transformations when safely available.
- Distinguish absent, null, empty, zero, unlabeled and censored outcomes. Check
  whether transformations use only information available at decision time.
- Inspect label availability/quality, selection bias and train/deployment shift
  where they affect the stated task. Statistics alone do not establish cause or
  authorize automatic unit/time corrections without definition evidence.
- Use only applicable checks. Record NOT_APPLICABLE with a reason for absent
  temporal/ML/join structure; keep material unknowns UNVERIFIED. Do not require
  every task to resemble semiconductor sensor modeling.

## Evaluation and grader validity

Trace the original metric, direction, units, weights, penalties and invalid-output
handling into the actual evaluator. Distinguish official score, estimated business
effect and local declared-check coverage; unknown weights remain unknown.
Current and naive baselines are useful controls, not proof the grader is correct.

For an internal grader, test small independent known-answer cases, arithmetic,
rankings and hard-constraint violations. Include deliberately wrong outputs that
could look attractive under an omitted cost/penalty; verify they are rejected or
scored as the original contract requires. Do not derive expected answers from
the candidate being evaluated. If no grounded oracle exists, disclose that limit
instead of manufacturing a numeric official score or confident improvement.

For learning/tuning tasks, separate training, method/hyperparameter selection and
final evaluation. Use time/group/lot/tool splits when the original data structure
requires them; fit preprocessing on permitted training scope only. Repeatedly
choosing settings by a later period makes it tuning data, not an untouched final
test. Keep final answers and author-only grading assets out of search/tuning.
Do not force a temporal split when no relevant temporal structure exists.

Bind baseline/current candidate, evaluator, data/split and option/budget scope.
Changed semantics or scope start a separate comparison series. Check uncertainty,
subgroup failures and metric gaming where consequential, without inventing extra
business objectives. Sampling cannot establish whole-dataset integrity.

## Return

Use the shared finding/disposition format with source/definition, minimal input,
expected versus observed, command/bounds and STATIC versus EXECUTED evidence.
Explain how a discovered data/evaluator defect could change the claimed result.
Report unrun checks and unresolved label/business truth separately from failures.
Recheck fixes against independent controls before FIXED; a new checkpoint follows
the active clean-review rule. Do not certify future performance or real ROI.
