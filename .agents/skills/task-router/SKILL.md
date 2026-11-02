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

Return to `.hackathon-kit/run/STATE.md` or SPEC_DRAFT:
- task type(s)
- classification evidence
- scoring-relevant path
- relevant playbooks
- explicitly **not applicable** playbooks
- highest-risk boundaries

Activation rule:
- use a domain playbook only when task material or grader contract supports it
- if classification confidence is low, stay with core skills instead of stacking multiple playbooks

Reference `.hackathon-kit/references/task-types.md` when present.
