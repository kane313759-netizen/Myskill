---
name: data-profiler
description: Profile provided CSV, JSON, spreadsheet, or structured files before business logic is written.
---

Inspect actual supplied data.

Report:
- files and sizes/row counts
- columns/keys and inferred types
- candidate primary/join keys
- null/blank counts
- duplicate keys
- distinct counts
- min/max/ranges
- inconsistent formats
- impossible or suspicious values
- cross-file referential gaps
- resource counts that may imply hidden operational limits

Separate observations from business-rule assumptions.

When useful, run local scripts under .hackathon-kit/scripts or create a minimal deterministic profiler in the workspace.
