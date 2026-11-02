---
name: optimization
description: Review assignment, routing, scheduling, capacity, allocation, or optimization tasks without assuming domain-specific limits.
---

Identify:
- decision variables
- hard constraints
- soft objectives
- objective function
- tie-breakers
- feasibility rules
- resource counts
- human burden
- baseline solution
- sanity metrics

Before trusting an optimum, attack:
- unlimited free resources
- one metric improving while another collapses
- max vs average
- unassigned entities
- utilization
- fairness
- pathological but mathematically valid solutions

Do not invent resource limits, costs, fairness requirements, penalties, or tie-breakers. Unsupported concerns remain questions or explicit ASSUMPTIONs; they must not alter the official objective or feasible set. Apply a penalty/tie-breaker only when task/grader evidence or an explicit allowed clarification supports it, and verify that it preserves the official scoring contract.
