---
name: tool-inventory
description: Explain unfamiliar mandatory technologies and locate their real role in the current project without changing implementation.
---

Read README, Dockerfiles, manifests, env examples, configs, and code references.

For each unfamiliar technology/tool explain:
- why this task uses it
- where it sits in the system
- input
- output
- what/where it stores
- what breaks if it fails
- actual files/config that use it

Then map it onto:
input → processing → storage → output → external connections

Do not modify code while performing discovery.
