---
name: algorithm-cli
description: Use only for exact-input/output algorithm, CLI, parser, or hidden-test tasks where contract fidelity, complexity, determinism, and malformed inputs dominate.
---

Applicable only if task-router identifies algorithm/CLI/parser evidence.

Prioritize:
- exact stdin/file/argument contract
- exact output formatting/order
- deterministic behavior
- integer/float precision and tolerance
- empty/min/max inputs
- malformed input behavior when specified
- time/memory complexity at plausible hidden-test scale
- locale/encoding/newline differences

Do not introduce UI, DB, Docker, or operational realism concepts unless the task actually requires them.
