---
name: constraint-discovery
description: Find explicit constraints, implicit reality candidates, soft quality goals, extreme-value failures, and objective loopholes before or during implementation.
---

Do not implement while running this skill.

# Extract explicit constraints

Look for:
- counts and resource limits
- min/max values
- capacity
- time windows
- distance
- uniqueness / one-to-one rules
- exclusions
- priority
- failure behavior
- date/time semantics
- persistence / restart behavior
- external-system boundaries

For each record:
constraint | hard/soft | evidence | violation impact | implementation location | test

# Find implicit reality candidates

Scan:
- resource count
- cost/budget
- time
- physical limits
- human waiting/walking/detour/repetition
- fairness
- utilization
- scale
- retry/duplication
- operations feasibility

Never convert an unstated candidate into a hard fact.

# Extreme-value attack

Ask:
- What can be increased without limit to improve the objective?
- What can approach zero and create a pathological solution?
- Can averages look good while max values become absurd?
- Can the system satisfy rules with a result no operator/user would accept?

For each candidate report:
problem | why suspicious | pathological example | hard/soft/question recommendation | metric/test
