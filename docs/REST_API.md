# TKAI Studio REST API v2.1

The Studio REST API is frozen as a local, SDK-only contract. All endpoints are
mounted below the configured `api_prefix` (default `/api`) and return JSON.

## Response envelopes

Successful responses use `success`, `data`, `request_id`, and UTC `timestamp`.
Error responses use `success: false`, an `error` object with `code` and
`message`, plus `request_id` and UTC `timestamp`. Errors never include a stack
trace, credential, or request body.

## Endpoints

- `GET /health`, `GET /system`, `GET /version`
- `POST /projects`, `GET /projects`, `GET/PATCH/DELETE /projects/{project_id}`
- `POST /workflows`, `GET /workflows`,
  `GET/PATCH/DELETE /workflows/{workflow_id}`
- `POST /executions`, `GET /executions`,
  `GET /executions/{execution_id}`

Projects accept `project_id` (optional), `name`, `description`, and `metadata`.
Workflows require `workflow_id`, `project_id`, and `name`; optional visual nodes
and edges are structurally validated. Executions require an existing
`workflow_id` and run only through an explicitly supplied `SDKStudioGateway`.

## OpenAPI

`studio.backend.api.openapi_schema(settings)` emits the deterministic OpenAPI
3.1 document with Success and Error schemas. A FastAPI host may expose the same
contract at its configured `openapi_url`; FastAPI remains an explicit Studio
host dependency.

## Limitations

This freeze does not add authentication, persistence, async queues, WebSocket
execution, external Providers, Agent chat, or frontend integration.
