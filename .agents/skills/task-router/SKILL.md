---
name: task-router
description: Classify an unfamiliar task after grader intake and select only evidence-supported playbooks; do not activate domain playbooks merely because their vocabulary appears once.
---

Read `.hackathon-kit/run/GRADER.md` and task material.

Classify one or more:
1. algorithm / CLI / parser
2. data analysis / anomaly detection
3. ML / data science
4. optimization / assignment / scheduling / operations
5. web app / CRUD / dashboard
6. API / external integration
7. AI agent / chatbot / RAG
8. automation / scheduler / workflow / data pipeline
9. security / auth / permission
10. document / multimodal extraction or transformation
11. debugging / repair of existing repository
12. mixed

Return classification to ORCHESTRATOR for STATE.md and to MAIN for SPEC_DRAFT:
- task type(s)
- classification evidence
- scoring-relevant path
- relevant playbooks
- explicitly **not applicable** playbooks
- highest-risk boundaries

Use the task toolchain only by default: original supplied/declared/required tools,
kit helpers and the standard library. Optional additions are NONE, even when a
catalog helper happens to be installed. Do not scan PATH, consult the optional
catalog, fetch upstream workflows or try an optional helper during normal routing.
Python/CSV/JSON/PDF vocabulary or possible convenience is not a requirement.

Preserve ordinary task-required README/manifest/official setup, including permitted
dependency installation. For a new project without a toolchain, choose the smallest
implementation route that meets the actual deliverable; justify a genuinely needed
product dependency in normal SPEC/CP1. Do not relabel an optional analysis/lint/agent
helper as required merely for speed or polish. Missing required capability remains
an explicit blocker or valid partial-result limitation, not a silent skip.

Return the task tools with original source evidence, required setup/availability,
fallback, important data/side-effect guards and budget. MAIN records the compact plan
in SPEC_DRAFT's existing verification plan, preserving headings. Later material
changes use existing ownership/reopen rules. No new checkpoint or routine technical
approval is needed. `.hackathon-kit/references/optional-tools.md` is retained for separate preparation
or a new explicit request for a particular optional mode, not automatic adoption.

Activation rule:
- use a domain playbook only when task material or grader contract supports it
- if classification confidence is low, stay with core skills instead of stacking multiple playbooks

Reference `.hackathon-kit/references/task-types.md` when present.
