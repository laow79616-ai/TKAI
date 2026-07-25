# TKAI Studio V2.1 RC-1 Integration Baseline

## Baseline

- Baseline commit: `a79da87` (`feat(studio): establish agent chat`)
- Validation branch: `feature/v2.1-studio-architecture`
- Scope: offline integration and compatibility validation only.

## Completed Studio modules

Studio Architecture, backend server foundation, frozen REST API, React frontend
foundation, Workflow Designer, Execution Monitor, and Agent Chat are present as
independent Studio product layers. They consume public SDK boundaries and do not
modify the V1.x Runtime.

## Integration and compatibility results

The RC-1 suite validates the project/workflow/execution chain using an injected
public SDK `WorkflowRuntime`; CRUD controllers; health, system, and version
responses; stable request/error envelopes; repository concurrency; gateway
failure isolation; offline SDK examples; and static Designer/Monitor/Chat
contracts. The frozen REST route inventory, OpenAPI schema, response envelope,
SDK public API, and V1.x Runtime are unchanged.

Lifecycle validation covers the existing explicit gateway ownership and
idempotent Studio dependency shutdown semantics. Reference repositories use
bounded concurrent operations and lock-protected in-memory state. A failed
gateway request retains an exception cause and a fresh, independently composed
Studio host remains usable.

## Frontend validation scope

Python static contract checks verify typed REST client use, component and store
declarations, no direct `fetch` bypass in feature stores, and no default
polling/timer side effect. This environment has no installed frontend
dependencies, so npm/Vite/TypeScript/ESLint execution is not claimed; those
checks remain required in a Node-enabled frontend build environment.

## Quality results

The final RC-1 gate runs `pytest`, `ruff check .`, `black --check .`,
`mypy src`, and `git diff --check`. The dedicated Studio integration suite is
also run three times. All checks are offline and use no API key, real Provider,
network service, server start, or database.

## Known limitations

- No authentication, database persistence, WebSocket, background polling, or
  real-time execution monitor.
- No real Provider, Agent Chat transport endpoint, streaming chat, or automatic
  SDK/Provider configuration.
- Workflow Designer, Execution Monitor, and Agent Chat are reference frontend
  models, not browser-rendered production features in this environment.
- No Node/Vite validation in this environment.

## RC-2 recommendation

Ready for RC-2 performance and reliability validation after frontend tooling is
validated in a Node-enabled target environment. No release blocker was found in
the offline RC-1 integration scope.
