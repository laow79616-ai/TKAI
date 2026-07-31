# TKAI Business Platform V2 API Guide

Authenticate with `POST /auth/login`, then send `Authorization: Bearer <token>`,
`X-Tenant-ID`, and `X-Workspace-ID`. Use `/business/v2/records` for GET/POST,
`/business/v2/records/{record_id}` for GET/PATCH/DELETE (soft archive),
`/business/v2/dashboard` for persisted KPIs, `/business/v2/audit` for history, and
`/business/v2/reports/export` for redacted JSON. The compatibility API remains at
`/business/v1`. OpenAPI is available at `/openapi.json` and in the release artifact.
Secret values are rejected; use opaque keys ending in `_ref` inside `references`.
