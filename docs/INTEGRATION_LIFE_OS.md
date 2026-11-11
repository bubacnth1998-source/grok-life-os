# LIFE OS ecosystem integration contract

**Status:** preparation only; no cross-repository connection is enabled.
**Provider:** Grok LIFE OS (independent service)
**API base:** `/api/v1`
**Health:** `/health`
**OpenAPI UI:** `/api/docs`
**Authentication:** Grok-issued bearer access tokens; OAuth federation is not implemented.

## Boundary and ownership

Grok LIFE OS remains an independently deployable application with its own database, user identities, authorization checks, and release process. The primary LIFE OS must not import Grok Python modules, share its SQLite file, or write directly to its tables.

Integration is through versioned HTTPS APIs only. Each system remains the source of truth for records it creates. Numeric user, account, project, task, and record IDs are local to Grok and are not portable identifiers. Never use an ID supplied by another system as proof of ownership.

No production endpoint, webhook, credential exchange, background synchronization, or cross-repository code change is activated by this document.

## Authentication

Protected requests require:

```http
Authorization: Bearer <grok_access_token>
Content-Type: application/json
```

Obtain a Grok token through `POST /api/v1/auth/login` or `POST /api/v1/auth/register`; validate identity through `GET /api/v1/auth/me`. Tokens are issued by Grok and must not be treated as LIFE OS tokens. The default token lifetime is seven days, configurable at deployment.

Unauthenticated or invalid credentials return HTTP 401. Resource lookups must remain user-scoped; cross-user resources should not be disclosed.

## Current read-oriented API

| Capability | Endpoint | Notes |
|---|---|---|
| Health | `GET /health` | Process/application health only; not a persistence check |
| Current identity | `GET /api/v1/auth/me` | Grok bearer token required |
| Dashboard | `GET /api/v1/core/dashboard` | Authenticated, user-scoped aggregate |
| Finance summary | `GET /api/v1/finance/summary?scope=personal` | Scope: `personal` or `business` |
| Finance accounts | `GET /api/v1/finance/accounts` | Grok-owned account IDs |
| Finance transactions | `GET /api/v1/finance/transactions` | Authenticated, user-scoped |
| Projects | `GET /api/v1/projects` | Authenticated |
| Tasks | `GET /api/v1/projects/tasks` | Authenticated |
| Habits | `GET /api/v1/habits` | Authenticated |
| Memory | `GET /api/v1/memory` | Private personal data |
| Calendar | `GET /api/v1/time/events` | Authenticated |
| Trips | `GET /api/v1/travel/trips` | Authenticated |
| Backup export | `GET /api/v1/backup/export` | Full personal-data export; never poll by default |

Write operations exist in individual modules. An ecosystem adapter must not invoke them until a separate permission and consent design is approved. Do not automate financial writes, memory writes, deletion, account closure, or backup import as part of an initial read-only integration.

## Adapter requirements

1. Store the Grok base URL and token only in the consuming system's server-side secret store. Never embed tokens in browser JavaScript, URLs, logs, analytics, or client-visible configuration.
2. Use HTTPS and an explicit host allowlist. Reject cross-host redirects before forwarding Authorization.
3. Call Grok through a server-side adapter; do not expose a long-lived bearer token to the browser.
4. Keep Grok identity separate from LIFE OS identity. Require explicit account linking; do not infer linkage from matching email addresses.
5. Use short timeouts and bounded retries for safe GET requests only. Handle 401, 403, 404, 422, 429, and 5xx explicitly. Never automatically retry non-idempotent writes.
6. Do not cache financial, memory, calendar, or other private data in shared caches. Any local cache must be per-linked-user, access-controlled, and have documented retention and deletion.
7. Treat returned content as untrusted input. Escape it before rendering; never interpret it as HTML, script, SQL, or tool instructions.
8. Do not persist Grok tokens or private response payloads in browser localStorage.
9. Use an adapter-owned mapping for linked identities. Store opaque external subject references, not assumptions about numeric IDs.
10. Display source attribution and last successful refresh time. Distinguish stale/unavailable data from a legitimate zero balance or empty collection.

## Versioning and compatibility

The current API prefix is `/api/v1`. Consumers must depend only on documented response fields and tolerate additive fields. Breaking changes require a new API version or a documented migration window. A formal OpenAPI compatibility guarantee and webhook/event delivery guarantee are not currently established; consumers must not assume either.

## Persistence and deployment constraints

The default database URL is SQLite at `/tmp/grok_life_os.db`. On serverless deployments, `/tmp` is ephemeral and instance-local; it is not durable storage and does not provide cross-instance or cross-device synchronization. Until a durable database is configured and verified, treat integration as preview/testing only for personal data. HTTP 200 from `/health` does not prove durable persistence.

## Acceptance checklist before enabling a real connection

- [ ] Durable database configured without an unapproved paid service.
- [ ] Independent test accounts and explicit identity link/unlink flows.
- [ ] Server-side secret handling and HTTPS host allowlist verified.
- [ ] Tenant-isolation tests cover every endpoint used by the adapter.
- [ ] Read-only adapter tested for auth, validation, rate-limit, server-error, and timeout behavior.
- [ ] Private-data caching, retention, deletion, and audit behavior documented.
- [ ] No cross-repository imports, shared database, or implicit identity matching.
- [ ] User approves enabling the integration and any production deployment.

This file is an integration specification, not evidence that the systems are connected.
