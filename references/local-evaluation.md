# Local evaluation from the pre-edit baseline

Read EXAM_POLICY.md first. This is part of the existing intake, verification and
review workflow, not an extra checkpoint, role or required score target.

## Choose the smallest useful evaluator

1. Prefer the task's visible grader/test commands and preserve their actual metric,
   native results and command evidence. An official visible result stays separate
   from a local proxy and never reveals hidden tests.
2. If useful checks are missing, MAIN may build a small task-local evaluator from
   explicit original requirements, independently justified expected results and
   already permitted task tools/stdlib. Do this before product edits where feasible.
   Do not recreate the whole hidden judge, invent official weights, install optional
   helpers, add domain preferences, or delay implementation for a large framework.
3. Record unavailable/unsafe/too-expensive checks with reasons. An unknown oracle
   remains unverified; the candidate's own output cannot become its expected answer.
   If a useful local evaluator cannot fit the budget, retain the existing baseline
   and the explicit gap. A numerical score is not mandatory gate evidence.

Use small known-answer cases, output/interface checks, confirmed hard constraints,
relevant boundary/invalid cases and preservation checks as appropriate to the task.
Expected rejection is a passing negative test when it matches the documented oracle;
an application exit of 2 is not universally a failed test. Inspect mutation/network
effects, resolve command paths against the recorded working directory, and isolate
temporary state before executing any check. Missing input/tool or a wrong invocation
is an invalid measurement, not evidence that the product earned zero official points.

## Freeze what makes a comparison meaningful

MAIN records the rubric, evaluator/fixture/config file paths and actual SHA-256
values in the existing GRADER.md or SPEC_DRAFT.md. Include the baseline report hash,
command/cwd/bounds, actual candidate source version/hash and input/policy/options
scope in BASELINE.md. A commit label alone does not identify dirty working files.
Use original validated input manifests/fingerprints when available; do not rehash
gigabytes after every small edit just for this summary.

At CP1, clean Constraint Red verifies requirement sources and oracles and inspects
the actual evaluator as a claim. Exercise a small known-good and known-bad control
when safely possible; a grader that accepts its own invented expected output is not
independent validation. Code Red checks relevant checker failures at CP2/CP3.

The normal gate binds five documents, not arbitrary external JSON/code files. The
recorded rubric/checker hashes therefore need checking against those actual files;
do not claim gate_check.py automatically freezes them. Freeze the evaluated rules
and baseline after CP1. MAIN authors these before CP1; Recorder alone persists later
score summaries/history from MAIN's actual command/results. Raw execution outputs
use explicitly assigned, isolated paths with one writer; no shared-note races.

If requirements, checker semantics, expected fixtures or evaluation scope change,
retain the old reports, disclose the change and apply normal material-change review.
Start a separate series. Re-evaluating preserved old outputs with a corrected grader
must be labeled a later re-evaluation; running current code cannot recreate a lost
pre-edit baseline. Never silently overwrite/relabel it to manufacture improvement.

## Read-only coverage helper

`local_score.py` summarizes explicit observation records. It does not execute checks,
import a task grader, install anything, access services or prove the observations
true. It displays **local declared-check coverage**, never an estimated official
hidden-test score. Unknown official weights remain unknown; keep visible official
metrics separately in BASELINE/VERIFY. A local 10/10 does not authorize submission,
waive P0/P1, or establish coverage of requirements missing from the rubric.

Fill the installed `run/LOCAL_RUBRIC.json` for the actual task. Minimal schema:

```json
{
  "version": 1,
  "unknowns": ["Hidden tests and their weights are not available."],
  "criteria": [
    {
      "id": "required_output",
      "description": "The required output can be checked.",
      "source": "Original task path/section with this requirement",
      "oracle": "Independent expected result and why it follows from that source"
    }
  ]
}
```

Every result identifies the actual evaluated version and stable evaluation scope:

```json
{
  "version": 1,
  "label": "baseline",
  "evaluated_version": "Actual candidate source hash, or UNKNOWN",
  "evaluation_scope": "Verified input/policy/options fingerprint, or UNKNOWN",
  "checks": [
    {"id": "required_output", "status": "FAIL", "evidence": "Exact command/cwd/native result and retained log path"}
  ]
}
```

Allowed statuses are PASS, FAIL, ERROR, SKIP and UNVERIFIED. Missing criteria become
UNVERIFIED. All declared criteria stay in the denominator; only evidenced PASS earns
a point. Empty criteria mean UNAVAILABLE, not 100%. Evidence strings are records to
inspect, not automatically authenticated execution. UNKNOWN scope cannot support
a comparable delta. Do not use secrets or task contents in external reporting.
Keep evidence strings to concise native outcomes and local log references, not raw
datasets or long transcripts. Preserve raw logs separately and surface only summary,
delta, gaps and report paths to avoid filling the working context with score records.

Example during the permitted baseline stage, using actual local paths:

```bash
python -I -S -B .hackathon-kit/scripts/local_score.py \
  --rubric .hackathon-kit/run/LOCAL_RUBRIC.json \
  --results <baseline-observations.json> \
  --evaluator <actual-checker.py> --evaluator <small-expected-fixture.json>
```

Supply every file defining checker/oracle semantics; evaluator files are hashed,
never executed. Later use the same arguments with new observations and
`--compare <preserved-baseline-report.json>`. Capture stdout to a new uniquely named
report through its assigned writer; never redirect over the baseline or input files.
Use these isolated stdlib-only Python flags for this helper to avoid ambient
PYTHONPATH/site startup hooks; task-native tests still use their reviewed toolchain.
The helper rejects malformed/oversized inputs and nonregular/symlink target files,
and bounds evaluator hashing. It is not an OS sandbox or a proof that all relevant
checker dependencies were supplied.

Comparison requires the same rubric bytes, actual evaluator files/hashes and known
evaluation scope. A sample/full, policy or bound change is a separate series, not
score improvement. Candidate code versions may change and must be recorded. Changed
rules/checkers/scope suppress delta; do not refresh hashes merely to force comparison.
Loss of a prior PASS is lost verified coverage to investigate, not automatically a
proved product bug when a check could not run.

Exit 0 means every declared check passed and any requested comparison is comparable.
Exit 1 means a valid record with failures, incomplete coverage, unavailable coverage
or a non-comparable series. Exit 2 means invalid input/tool invocation. Preserve the
native checker outcome as well; helper output is not a replacement for it.

## Cadence and final explanation

Record baseline, first end-to-end and final results under the same rules. Run cheap
affected checks after meaningful changes; reuse unchanged evidence with its version
label. Full-scale/heavy evaluations run only when relevant changes, failures or the
final contract justify the cost. Never run the full suite after every edit or wait
for a numerical target at the expense of official submission/follow-up time.

Recorder places the history in VERIFY.md, with source version, scope, report/evidence
paths, visible official metric if any, local coverage, gaps and comparable delta.
Prepare a plain explanation of before/after, a real boundary/negative test and what
was not checked. A proxy score is not proof of future accuracy, human UI verification
or a personal action by the participant.
