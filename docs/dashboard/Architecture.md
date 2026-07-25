# Marketplace Server Dashboard MVP

## Scope

The Dashboard is an independent React, TypeScript, Vite, and TailwindCSS source
application in `dashboard/frontend`. It consumes only the Marketplace Server V2
HTTP API and does not import or modify any Server Foundation service.

## Routing and pages

- Login (`/login`)
- Dashboard Home (`/dashboard`)
- Registry (`/registry`)
- Publishers (`/publishers`)
- Packages (`/packages`)
- Versions (`/versions`)
- Search (`/search`)
- Statistics (`/statistics`)
- Health (`/health`)
- 404 fallback

The shell has a left navigation sidebar, top header, and central routed content.
Reusable components include `Card`, `Table`, `SearchBar`, `Loading`, and
`ErrorBoundary`.

## API and authentication

`MarketplaceApiClient` is the sole HTTP boundary. It calls the existing
`/auth/login`, `/auth/me`, `/auth/logout`, resource, health, version, search,
and statistics endpoints. `AuthProvider` stores the opaque Bearer token in
browser `sessionStorage` and supplies it as `Authorization: Bearer <token>` on
subsequent requests. Tokens are never embedded in source or sent to another
service.

## Development

In a Node-enabled environment run `npm install`, then `npm run typecheck`,
`npm run lint`, and `npm run build` from `dashboard/frontend`. The repository's
current offline validation environment has no Node/npm executable, so Python
static contract tests validate the source layout and endpoint declarations.

## Limitations

This MVP has no server-side rendering, persistent browser state, advanced data
tables, real-time updates, role-aware navigation, dashboard write operations,
or packaged frontend build output.
