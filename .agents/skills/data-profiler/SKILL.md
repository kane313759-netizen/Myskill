---
name: data-profiler
description: Profile explicit provided data files safely and boundedly when the task actually contains structured data; do not recursively scan a repository.
---

Read `.hackathon-kit/run/GRADER.md` first.

Use only explicit task data files or paths identified from task evidence.
Do not recursively scan `.`, `node_modules`, environments, build output, or the repository.

When useful run:
`python .hackathon-kit/scripts/profile_data.py <explicit files>`

The helpers read at most `--max-rows` records per selected table (default 50000) and refuse JSON over `--max-json-bytes` (default 52428800). `profile_data.py` accepts at most `--max-files` files (default 32). These are sample/JSON-input limits, not a guarantee of total memory use for arbitrarily wide rows or compressed workbooks. Choose smaller limits for wide data and do not raise limits automatically after an error.

Use input-specific options only when the original file/task supports them:
- `--encoding cp949` or another explicit encoding when known. Automatic text decoding tries UTF-8/CP949; it cannot prove the intended encoding.
- `--records-key data.items` or `--records-key /data/items` to select JSON records. Ambiguous record arrays require an explicit choice; do not silently analyze metadata as records.
- `--list-sheets`, then `--sheet "Sheet name"` or `--all-sheets` for workbooks. Multiple sheets require a choice, and each selected sheet is summarized separately. XLSX/XLSM reading requires existing `openpyxl`; do not install dependencies into the task project merely to profile data.
- Repeat `--null-token VALUE` only for task-defined missing markers. Matching is exact and case-sensitive after stripping cell whitespace; values such as `NA` or `0` are not automatically missing.
- Numeric summaries skip identifier-like and leading-zero columns by default. Use `--include-id-like` only after confirming that numeric magnitude is meaningful.

`sanity_check.py <explicit file>` accepts the same read/selection options and reports numeric scale, not automatic business-rule violations. Do not send files to external profiling services.

Report:
- sampled row count / cap
- columns/keys and likely semantic type
- candidate join keys
- null/blank
- duplicates in the bounded sample, not a global uniqueness proof
- distinct/sample distribution and any distinct-count cap reported
- numeric range only for fields that are meaningfully numeric
- cross-file referential gaps when explicitly checked
- observations that suggest a question, clearly separated from confirmed business rules

Do not infer business constraints from a surprising statistic alone.
Record the file, selected table/path, options, sampled row cap, and relevant output
as evidence for MAIN/Recorder in the second preliminary, or for the current writer
in FINALS_RUN.md in finals. A partial sample does not establish whole-file integrity
or cross-file referential correctness.
