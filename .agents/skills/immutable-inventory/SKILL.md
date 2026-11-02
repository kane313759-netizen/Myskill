---
name: immutable-inventory
description: Identify files, interfaces, schemas, tests, and contracts that should not be changed casually in an unfamiliar task.
---

Read `.hackathon-kit/EXAM_POLICY.md` and `.hackathon-kit/run/GRADER.md` first when present.

Inspect task instructions, tests, schemas, public APIs, generated files, lockfiles, fixtures, sample I/O, and submission paths.

Write `.hackathon-kit/run/IMMUTABLES.md`:
- explicit do-not-modify items
- public contracts that hidden tests may rely on
- tests/fixtures that must not be weakened or hard-coded around
- generated/vendor/build artifacts that should not be edited manually
- uncertain items labeled ASSUMPTION, not fact

Do not declare a file immutable merely because it looks important.
Use evidence paths/locations where possible.
