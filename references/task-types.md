# Task type routing

| Type | Typical signals | Conditional playbooks |
|---|---|---|
| Algorithm / CLI / parser | stdin/stdout, exact format, complexity, deterministic function | algorithm-cli, verification |
| Data analysis / anomaly | CSV/JSON/XLSX, aggregation, detection | data-profiler, verification |
| ML / data science | train/valid/test, metric, seed, model artifact | ml-data-science, data-profiler |
| Optimization / operations | routing, schedule, allocation, capacity, objective | optimization, constraint-discovery |
| Web app / CRUD | forms, login, dashboard, persistence | web-app, verification |
| API integration | endpoint, token, request/response | api-integration, debugging |
| Agent / chatbot / RAG | model, tools, retrieval, chat history | agent-chatbot, api-integration |
| Automation / data pipeline | cron, queue, ETL, workflow, recurring task | automation, verification |
| Security / auth | permissions, secrets, attack surface, policy | security-review |
| Document / multimodal | PDF/image/text extraction/transformation | document-processing |
| Debug existing repo | failing tests, broken feature, patch-only task | debugging, verification |
| Mixed | several are materially present | choose only the minimum required set |

## Activation rule

A playbook is active only if task/grader evidence supports it.
If a type is not supported, mark it NOT_APPLICABLE instead of running its checklist.
Mixed does not mean “run every playbook.”
