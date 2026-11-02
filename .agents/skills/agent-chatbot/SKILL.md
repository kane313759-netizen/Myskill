---
name: agent-chatbot
description: Design or review AI agent, chatbot, RAG, or tool-calling tasks while checking state, grounding, tools, safety, and API boundaries.
---

Verify which model/API/tool endpoints the task explicitly provides or allows.

Map:
user → UI → backend → agent/model → tools/knowledge → response → conversation state

Check:
- system/developer instructions
- conversation state/history
- tool permissions
- grounding/source of truth
- retrieval boundaries
- tool-call validation
- hallucination/failure behavior
- timeout/rate limits
- secret handling
- user-data retention
- external data transmission
- tests for deterministic non-model logic

Do not silently add an external AI provider that the task/rules do not allow.
