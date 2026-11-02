# CODE RED — Terra 5.6

Independent review only. **Do not edit source.**

Attack:
- requirement implementation gaps
- boundary/off-by-one
- null/blank/invalid format
- duplicate/missing/conflicting records
- persistence/restart/retry
- module wiring
- regression
- unsafe failure behavior
- tests with incorrect expectations

Report only:
severity | reproduction | file/line evidence | impact | minimal fix direction

If the issue is primarily a business/realism constraint, mark: Constraint Red review needed.
