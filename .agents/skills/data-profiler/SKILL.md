---
name: data-profiler
description: Profile explicit provided data files safely and boundedly when the task actually contains structured data; do not recursively scan a repository.
---

Read GRADER.md first.

Use only explicit task data files or paths identified from task evidence.
Do not recursively scan `.`, `node_modules`, environments, build output, or the repository.

When useful run:
`python .hackathon-kit/scripts/profile_data.py <explicit files>`

The helper is bounded by row limits and refuses oversized JSON by default.

Report:
- sampled row count / cap
- columns/keys and likely semantic type
- candidate join keys
- null/blank
- duplicates in sample
- distinct/sample distribution
- numeric range only for fields that are meaningfully numeric
- cross-file referential gaps when explicitly checked
- observations that suggest a question, clearly separated from confirmed business rules

Do not infer business constraints from a surprising statistic alone.
