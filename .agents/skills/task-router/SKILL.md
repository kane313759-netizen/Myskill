---
name: task-router
description: Classify an unfamiliar task before implementation and select only the relevant playbooks.
---

Read the task brief, provided files, existing code, config, tests, and example outputs.

Classify as one or more:
1. data analysis / anomaly detection
2. optimization / assignment / scheduling
3. web app / CRUD / dashboard
4. API / external integration
5. AI agent / chatbot / RAG
6. debugging / repair
7. automation / scheduler / workflow
8. mixed

Return:
- task type(s)
- business problem in one sentence
- expected input and output
- storage/state needs
- external connections
- mandatory tools
- highest-risk boundaries
- relevant skills to invoke next

Do not infer domain rules that are not supported by task material.
