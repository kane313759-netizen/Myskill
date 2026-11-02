---
name: debugging
description: Diagnose an unknown failure by evidence before editing, then apply the smallest justified fix and rerun regressions.
---

Use:
symptom → failing boundary → hypotheses → discriminating test → root-cause evidence → minimal fix → regression test

Do not repeatedly patch symptoms.

Separate, when relevant:
browser/client cache | cookie/session | frontend | API | backend | DB/data | runtime/container/build cache | external dependency

After two failed small fixes or when multiple modules are implicated, escalate analysis to MAIN Sol.
