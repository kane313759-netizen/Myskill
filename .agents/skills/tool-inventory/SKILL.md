---
name: tool-inventory
description: Explain unfamiliar mandatory technologies and locate their real role in the current project without changing implementation.
---

Read the task README and the manifests/config/code references that actually exist. Inspect Dockerfiles only when the task uses containers. Do not dump environment values, credential files, or secrets.

This skill explains evidenced project technologies under task-router's task-tools-only
default; it does not recommend additional catalog helpers. The similarly named PATH
script is a separate manual diagnostic, absent from normal startup. It only observes
candidates and never chooses, runs, installs or approves a tool.

For each unfamiliar technology/tool explain:
- why this task uses it, or UNKNOWN when the reason is not evidenced
- where it sits in the system
- input
- output
- what/where it stores
- what breaks if it fails
- actual files/config that use it

Then map it onto:
input → processing → storage(if any) → output → external connections(if any)

Do not modify files or change implementation decisions while performing discovery.
Return source-linked facts to MAIN/Recorder in the second preliminary, or to the
current writer for FINALS_RUN.md in finals; a technology appearing in a dependency
list does not prove it is used on the scoring path. Verify model/runtime selection
from actual available evidence rather than the preferred role label.
