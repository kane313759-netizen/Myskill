---
name: security-review
description: Use only when authentication, authorization, secrets, permissions, or security behavior is materially part of the task or grader.
---

Applicable only with task/grader evidence.

In finals this is a domain checklist, not an independent SECURITY_RED receipt.
Use the current kit's references/finals-reviews.md for actual activation and
dispatch `security-redteam` only on evidenced conditions; do not relabel this
checklist or the writer's self-check as a separate security review.

Check:
- authentication vs authorization
- trust boundaries
- secret placement
- input validation
- privilege/role checks
- sensitive-data leakage
- path/file access
- injection risks relevant to the actual stack
- session/token expiry and replay when applicable
- safe error messages

Do not turn this into a generic penetration test if security is not part of the task.
Do not use external scanners/services that would transmit exam data.
