# Local evaluation validation — r7.2 candidate

This is a local candidate, not a change to the pinned GitHub r7.1 exam version.
EXAM_POLICY.md is unchanged (SHA-256
`b4deca2c78495bee0d19d0fbbfea797e65d49075aae461c80d21651f9b6ed558`).
The existing three checkpoints, ownership rules and official exam limits remain.
The initial results below are preserved. A subsequent
[full-source review](r7.2-full-review.md) adds runtime boundary corrections and broader
checks; use the exact review commit's CI status for later cross-platform results.

## Executed checks

- Final Linux/Python 3.12 suite: **126 tests, 125 passed, 1 skipped** in 14.551 seconds.
  The skip is the unavailable PowerShell executable, not a passing PowerShell check.
- New local-score suite: 29 passing tests for fixed-denominator coverage, honest
  missing/skipped results, invalid/duplicate inputs, current version and scope,
  comparison changes, special files, byte limits and read-only execution audit.
- Real unpacked-distribution integration: install the candidate, run actual checks
  against an incomplete small integer program, record 0/3, correct the program and
  record 3/3 under unchanged checks/scope. Native command records and actual source
  hashes distinguish the versions. Reinstall and cleanup/backup preserve the baseline
  and filled rubric; no installed helper bytecode cache is created.
- New helper/tests and the updated integration test parse with Python 3.8 grammar.
  This is not a Python 3.8 runtime or Windows execution claim.

## Independently reproduced and corrected defects

1. ASCII JSON escaping made some valid Unicode observations produce a baseline too
   large for its own comparison input limit. Keep rubric/results bounded to 1 MiB,
   with a separate 8 MiB prior-report/output cap including platform newlines.
   Independent Korean (1,081,046 bytes) and non-BMP (2,161,046 bytes) baselines now
   compare unchanged with exit 0 and zero delta, without baseline mutation.
2. Lexical `abspath` could change the meaning of a parent-symlink/`..` evaluator
   argument and hash another file. Check the original final component, resolve the
   actual filesystem identity, then hash the actual evaluator. Independent replay
   detects its change as non-comparable with exit 1/no delta. Final symlink targets
   remain rejected. Historical evaluator paths are not opened; deleted or FIFO
   replacements yield non-comparable reports without blocking.

The independent reviewer re-executed both original counterexamples and five focused
regressions after the fixes. No remaining supported defect was found in those paths.

## Limits

- No Windows or Python 3.8 runtime was available in this initial local validation.
  Its results alone do not establish the release CI matrix; later status belongs
  to the full-review commit's checks.
- No new complete 180-minute agent/nondeveloper rehearsal was run with r7.2.
  The earlier large composite mock used r7.1; its scores are not r7.2 validation.
- The helper summarizes records. It cannot authenticate execution, the supplied
  scope/version labels, complete dependency lists, or the correctness of an oracle.
  Original evidence and independent review remain necessary.
- Local coverage is not official/hidden score, proof of all requirements, a manual
  UI check, a waiver of a blocker, or proof of a real person's written-test ability.
