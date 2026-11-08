---
name: debugging
description: Diagnose an unknown failure by evidence before editing, then apply the smallest justified fix and rerun regressions.
---

Use:
symptom → failing boundary → hypotheses → discriminating test → root-cause evidence → minimal fix → regression test

Do not repeatedly patch symptoms.

Separate, when relevant:
browser/client cache | cookie/session | frontend | API | backend | DB/data | runtime/container/build cache | external dependency

After two failed small fixes or when multiple modules are implicated, obtain fresh
analysis before another patch. In the second preliminary, escalate to MAIN Sol
under its ownership protocol. In finals, keep the current single writer and use
only reviewers/models permitted by the active finals rules; if unavailable,
perform an explicitly labeled self-check rather than waiting for that role.
