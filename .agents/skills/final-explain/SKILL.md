---
name: final-explain
description: Prepare the participant for the official no-AI written follow-up using only actual task evidence, code, tests, decisions, and directly verified behavior.
---

This skill is for the pre-submission phase, not routine implementation.

Use:
- actual task/spec
- GRADER.md / BASELINE.md / CONSTRAINTS.md / DECISIONS.md / VERIFY.md
- current code/config
- business-contact answers
- things the user actually verified

Explain only components that exist:
1. problem solved
2. input
3. processing
4. storage/persistence if any
5. output
6. external connections if any
7. actual system boundaries
8. runtime/container only if present
9. important confirmed constraints
10. key design decisions and alternatives
11. what was verified
12. what remains unverified / limited

Compress to:
input → processing → storage(if any) → output → external(if any)

Then quiz the user one question at a time because the official follow-up cannot use AI/copy-paste.
Correct only the missing/incorrect part and keep answers short enough for a 5-minute written question.
