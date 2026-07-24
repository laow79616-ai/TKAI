# TKAI Studio Execution Monitor

The Studio Execution Monitor is a serializable, offline reference layer for
displaying records returned by the frozen Studio Execution REST contract. It is
a frontend product model only: it neither invokes the TKAI Runtime nor changes
execution state.

## Architecture

`studio/frontend/src/features/executions` separates domain models, deterministic
mapping helpers, pure store transitions, reference fixtures, and presentation
component contracts. React components receive props; mapping and the store do
not fetch directly. A caller injects the existing typed `StudioApiClient` into
the explicit `loadExecutions` and `applyExecutionPayload` actions.

## Status and timeline

The monitor presents `queued`, `running`, `completed`, `failed`, `cancelled`,
and `retrying` states. Unknown REST values are displayed as `unknown` rather
than converted into a new backend state. Timeline entries are sorted by valid
UTC timestamp, then supplied sequence, then identifier. Filtering is local and
deterministic. If the API lacks event detail, the monitor leaves a timeline
empty; reference fixtures are never represented as real runtime events.

## Tree, logs, trace, and metrics

The execution tree is a defensive hierarchy for execution, workflow, node,
tool, provider, memory, and plugin entries. Duplicate IDs and missing parents
are safely ignored; it does not execute or alter a Workflow Designer graph.

Logs support UTC ordering, stable de-duplication, level/text/node filters, and
metadata redaction for authorization, credential, secret, token, password, and
API-key-like fields. Traces and spans are local models only: missing span
parents become safe roots, duplicate spans are ignored, and no OpenTelemetry
collector is used. Metrics are derived only from supplied timeline/tree/log/
trace data; unavailable values remain `null` rather than inventing token, cost,
or provider-performance measurements.

## REST mapping and store

The monitor consumes only `POST /executions`, `GET /executions`, and
`GET /executions/{execution_id}` through the existing typed client. It preserves
the frozen response envelope's request ID and validates timestamps/statuses.
Error envelopes and client failures create a stable user-safe error state while
leaving prior data intact. Snapshots use JSON and restore validates the minimum
store shape.

## Reference data

Fixtures contain a completed task/provider/memory flow and a failed/retry flow.
They are deterministic UI/test/documentation examples, not runtime telemetry.

## Security and limitations

The monitor does not display secrets, authorization headers, credentials, or a
default exception stack. It has no WebSocket stream, default polling timer,
database persistence, live OpenTelemetry collector, real token/cost data, or
Agent Chat. Data comes only from the frozen API response or explicitly provided
reference fixtures. Node/npm are unavailable in this validation environment;
the Python static frontend contract tests cover source declarations, while Vite
typecheck/lint remains for a Node-enabled environment.
