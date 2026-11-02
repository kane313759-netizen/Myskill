---
name: api-integration
description: Design or review API and external-system integration tasks, especially auth, errors, timeouts, retries, idempotency, and data boundaries.
---

Map:
caller → endpoint → authentication → request → response → local processing/storage → user-visible result

Check:
- secrets location
- allowed endpoint/provider
- request/response schema
- validation
- timeout
- rate limit
- retry
- duplicate side effects / idempotency
- partial failure
- logging without leaking sensitive data
- offline/degraded behavior
- external data boundary

If exam rules restrict external services, verify that the endpoint is explicitly provided/allowed before use.
