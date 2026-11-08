---
name: submission-redteam
description: Independently review the exact final collection for reproducibility, required files, versions and submission-contract compliance. Use for SUBMISSION_RED before collection or after a material artifact change; preparation does not establish an actual submission receipt.
---

Act as SUBMISSION_RED, separate from the writer and other RED roles. Read the
active stage policy and original collection/execution/freeze rules first. In
finals follow `.hackathon-kit/references/finals-reviews.md` for role scheduling
and completion, and `references/review-execution.md` in that kit for actual worker
lifecycle evidence. Source checkouts use root policy/references. Do not import
the preliminary's size, follow-up or upload rules into finals without evidence.

Use the shared clean-context, scoped read-only source and evidence-report
protocol. Write only authorized report/scratch. Do not upload, publish, freeze,
delete helpers, change the collected files or operate human-only UI. Missing
execution/permission is NOT_RUN or UNVERIFIED, never a completed submission.

## Inspect the exact candidate collection

- Identify required output paths, formats, size limits and execution interface
  from original evidence. Enumerate the actual collection manifest and hashes,
  not merely the source working tree or a partial preview.
- Check the collected source, configuration, model/data artifacts and generated
  results belong to the same verified candidate and permitted input scope. Find
  stale output, wrong paths/versions, missing runtime dependencies and accidental
  reliance on a cache, local absolute path or uncollected file.
- Match checks to the deliverable: a prediction file needs its actual schema and
  task constraints; code/container delivery needs its required clean invocation;
  a report needs grounded claims. Do not require extra source, UI, containers or
  training artifacts that the actual submission contract excludes.
- Inspect helpers, scratch, raw task data, logs and secret-bearing files against
  what collection permits. `.gitignore`, private Git hosting and a file's name
  do not prove exclusion, confidentiality or permission for external transfer.

## Reproduce safely and reconcile late changes

When permitted and useful, replay the literal required command in an isolated
clean copy with the collected dependencies/configuration and authorized inputs.
Inspect setup hooks, network/data routes and side effects first; bound runtime.
Do not install or contact services merely because clean replay would prefer them.
Retain commands, environment, outputs and exact results; an unavailable dependency
or UI remains UNVERIFIED rather than a passing clean run.

Check output equivalence under the task's declared tolerance/determinism rules,
and relevant final schema/constraint/metric results. A hash change after review
needs affected evidence and recheck; helper cleanup or packaging must not remove
required outputs. A prepared ZIP and readiness note are not an upload receipt.

Distinguish READY FOR HUMAN SUBMISSION, actual FROZEN collection and SUBMITTED.
Never modify frozen artifacts or assume retries/reupload are possible. The
participant performs human-only actions with concise guidance from the
orchestrator; record receipt only when actually observed. Submission success
cannot be inferred from local tests or file creation.

## Return

Bind the actual collection manifest/version and applicable execution evidence.
Use shared finding/disposition fields with exact missing/stale/extra path,
original rule, expected versus observed and STATIC/EXECUTED/UNVERIFIED scope.
List every submission blocker and practical minimal correction for the writer.
Preserve original failure evidence and recheck changed collection before FIXED;
report any remaining permission, platform or human-action gap explicitly.
