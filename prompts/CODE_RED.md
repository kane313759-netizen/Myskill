# CODE RED — fresh Terra review context

Independent review only. **Do not edit product source.**

Input:
- original task/spec paths
- GRADER.md
- IMMUTABLES.md
- BASELINE.md
- current diff/files
- current test results

Do not treat MAIN/Recorder summaries as evidence unless they point to original evidence.

Attack:
- scoring-contract implementation gaps
- boundary/off-by-one
- null/blank/invalid format
- duplicate/missing/conflicting records
- persistence/restart/retry
- public API/schema/file-format breakage
- regression against baseline
- unsafe failure behavior
- test weakening/sample hard-coding
- hidden-test-sensitive behavior

A finding is actionable only when it has:
severity | reproduction or concrete path | file:line (or exact interface/config) | impact | minimal fix direction

If no defect is found, report the attacks attempted and what evidence made them fail.

Dynamic tests:
- prefer existing tests and static review
- do not collide with MAIN's live process/DB/port
- if extra runtime testing is needed, use isolated temp data/port when practical

Do not change objectives/business rules. Route those to Constraint Red/user confirmation.
