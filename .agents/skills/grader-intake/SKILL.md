---
name: grader-intake
description: Run first on an unfamiliar exam task to discover how it is graded/submitted, what must not change, and the baseline build/test state before implementation.
---

Read `.hackathon-kit/EXAM_POLICY.md` first if present.

# Goal

Before solving the business problem, determine **what success means in this task**.

Inspect, in this order when available:
- task/README/specification
- submission instructions and required filenames/paths
- existing tests and grading scripts
- sample input/output
- package.json / Makefile / pyproject / Docker/compose / CI config
- schemas and public interfaces
- existing build/run commands

# Output

Write/update `.hackathon-kit/run/GRADER.md` with:
- grading/submission contract
- required output files/commands
- visible tests and sample expectations
- likely hidden-test contracts (clearly labeled inference)
- time/memory/network/runtime constraints
- files/interfaces explicitly or implicitly unsafe to change
- unknowns that materially affect scoring

# Baseline

Before edits, run the strongest safe existing test/build commands that are already provided by the task.
Record commands and exact outcomes in `.hackathon-kit/run/BASELINE.md`.

Do not weaken/delete tests to make the baseline green.
If the baseline already fails, record that fact before implementation.

Completion condition:
- grading/submission contract is recorded, or explicitly marked UNKNOWN with evidence of what was inspected
- baseline is recorded, or the reason it could not be run is recorded
