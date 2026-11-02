---
name: web-app
description: Review web application tasks across UI, backend, authentication, storage, API contracts, and persistence.
---

Map:
browser/UI → frontend state → backend/API → business logic → storage → response

Check required screens/actions, validation, authn/authz, API contract, loading/empty/error states, persistence, duplicate submission, server trust boundaries, and frontend-vs-backend source of truth.

For login failures trace before editing:
browser → frontend → auth API → auth logic → DB/session.
