---
name: verification
description: Build evidence-based verification for requirements, constraints, regressions, persistence, and real-world sanity.
---

Create tests from the actual requirements.

Minimum categories:
- normal case
- boundary case
- invalid/missing data
- duplicate/conflict
- persistence/restart where relevant
- integration path
- reality/sanity metrics

Rule: each important hard constraint gets at least one test.

Distinguish:
- automated PASS/FAIL
- manual check required
- not tested

Never claim UI or browser behavior was verified unless it was actually observed by an allowed method or manually confirmed by the user.
