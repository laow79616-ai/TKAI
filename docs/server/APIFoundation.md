# Marketplace Server HTTP API Foundation

## Scope

The Server V2 HTTP API is an optional, read-only FastAPI host over the existing
Marketplace Server V6 Reference Foundation. It does not alter Foundation
services, access storage directly, start a listener, or perform network I/O.

## Application factory

`server.api.create_app()` builds one application with explicitly injected
`ApiDependencies`. Each instance owns its dependency container; there is no
global service singleton. FastAPI is an optional `tkai[server]` dependency. A
clear runtime error is raised only when a real host is requested without it.

## Routes and documentation

The first API surface has only read endpoints:

- `GET /health` — immutable snapshot from `ReferenceHealthService`.
- `GET /version` — Server and TKAI framework versions plus declared metadata.
- `GET /metadata` — descriptive Server Foundation capability metadata.
- `GET /openapi.json` and `GET /docs` — FastAPI-provided OpenAPI and Swagger UI.

## Middleware and errors

`RequestIdMiddleware` attaches one request-scoped ID and returns it as the
`X-Request-ID` response header without logging or retaining it. Foundation
domain errors are mapped to stable JSON error payloads by the exception
middleware and exception-handler registration.

## Limitations

This is a Reference Only HTTP layer. It has no resource write endpoints,
authentication, authorization, database, cache, background worker, WebSocket,
or deployment behavior. Resource APIs are intentionally deferred to Sprint-2.
