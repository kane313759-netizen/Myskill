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

Select optional helpers in the same pass. Start with NONE and the provided toolchain;
only a task/grader-backed need justifies another tool. Read the relevant portion of
`.hackathon-kit/references/optional-tools.md` when needed. If useful, run
`python -I -S -B .hackathon-kit/scripts/tool_inventory.py --task-root .` once: it observes PATH
candidates without executing them and does not verify identity/version, package
availability, compatibility or safety. It never grants approval or installs anything.

Return a compact decision with need/source, selected mode or NONE, actual availability/
provenance/version status, existing fallback, data/side-effect guards and reserved
time. MAIN records it in SPEC_DRAFT's existing verification plan for normal CP1
review, preserving headings. Prefer existing local tools; do not stack upstream
skills/hooks, separate AI, UI automation or external task-data routes. Later material
changes use existing ownership/reopen rules, with no extra checkpoint or participant
technical-approval step.

Activation rule:
- use a domain playbook only when task material or grader contract supports it
- if classification confidence is low, stay with core skills instead of stacking multiple playbooks

Reference `.hackathon-kit/references/task-types.md` when present.
