# Constraint discovery matrix

Scan every task across these dimensions.

| Dimension | Questions |
|---|---|
| Resource | Is a count limited? Can adding unlimited resources game the objective? |
| Cost | Is anything treated as free that would be expensive operationally? |
| Time | deadlines, windows, max wait, max duration, timezone |
| Capacity | seats, concurrency, storage, throughput |
| Physical | distance, location, impossible movement, device/runtime limits |
| Human burden | wait, walk, detour, repetitive steps, cognitive load |
| Fairness | is burden concentrated on a subset? |
| Scale | does solution still make sense at real data size? |
| State | persistence, restart, stale state, session |
| Retry | duplicates, idempotency, partial failure |
| Data | missing, duplicate, conflict, future/stale records |
| External | API availability, auth, timeout, rate limit |
| Security/privacy | secrets, PII, leakage, authorization |

Always distinguish:
- explicit hard constraint
- explicit soft objective
- implicit reality candidate
- open question

Never invent a numeric threshold just because one seems reasonable.
