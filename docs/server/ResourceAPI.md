# Marketplace Server Resource APIs

## Scope

Sprint-2 adds a read-only, GET-only HTTP contract over the existing Reference
Services. Routers receive their services through `ApiDependencies`; they never
open storage or change Server Foundation behavior.

## Endpoints

- `GET /registry`, `GET /registry/{registry_id}`
- `GET /publishers`, `GET /publishers/{publisher_id}`
- `GET /packages`, `GET /packages/{package_id}`
- `GET /versions`, `GET /versions/{version_id}`
- `GET /search`
- `GET /statistics`

`/search` accepts optional `keyword`, `target`, `publisher`, `package`,
`category`, `tag`, `version`, and `status` query parameters. Parameters are
validated with Pydantic contracts. Invalid values map to a stable HTTP 400
error; valid queries remain local, deterministic Reference Search calls.

## Response contracts

List and single-resource handlers use JSON-safe `ApiListResponse` and
`ApiResourceResponse` schemas. `ApiErrorResponse` documents stable error
payloads. All resource models are exported to OpenAPI when the optional
FastAPI host is installed.

## Limitations

The API is Reference Only and read-only. It contains no write methods,
authentication, authorization, persistent storage, background execution, or
network listener lifecycle.
