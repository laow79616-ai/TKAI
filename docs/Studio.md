# TKAI Studio architecture

TKAI Studio is an independent product layer above the public TKAI 2.0 SDK. It
does not import, construct, or modify the V1.x Runtime directly.

## Backend

The backend is structured around a dependency-free REST route inventory and an
optional FastAPI adapter. A Studio host installs FastAPI explicitly before
calling `create_fastapi_app`; FastAPI is not added to TKAI's core dependency
set. Authentication, sessions, and WebSocket delivery are protocols so a host
can supply its own implementation.

`SDKStudioGateway` is the only execution boundary. It receives an explicit
public SDK `Agent` and/or `WorkflowRuntime`; it never creates a provider,
runtime, credential, thread, or network connection implicitly.

The frozen REST inventory contains Project, Workflow, Execution, Health, and
System endpoints. The WebSocket protocol reserves asynchronous execution-event
delivery, without starting a server or socket loop. See
[REST_API.md](REST_API.md) for the frozen contract.

## Frontend

`studio/frontend` contains a React + TypeScript scaffold with a typed page
inventory for Dashboard, Projects, Workflow, Agents, Providers, Memory, Tools,
Plugins, Settings, and Logs. It includes no build output or dependency lockfile.
The reference product contracts are documented in
[WorkflowDesigner.md](WorkflowDesigner.md),
[ExecutionMonitor.md](ExecutionMonitor.md), and [AgentChat.md](AgentChat.md).
They do not alter the frozen REST API or execute a Runtime directly.

## Workflow designer model

`StudioWorkflow` and `StudioNode` are immutable visual declarations. Their
node kinds describe a designer canvas but do not compile to, execute, or alter
the SDK workflow engine. A future explicit compiler may translate a validated
designer graph to public SDK `WorkflowDefinition` objects.

## API and configuration

`StudioSettings` accepts an explicit mapping with a validated API prefix, host,
port, and session TTL. It does not read environment variables. Route ordering
and model snapshots are deterministic for offline API tests.

## Limitations

Sprint 1 provides architecture and contracts only: no authentication provider,
session storage, database, running FastAPI server, WebSocket server, React
rendering, drag-and-drop, Studio persistence, Studio deployment, or Enterprise
capability is implemented.

## Sprint 2 backend foundation

`create_studio_app()` builds an optional FastAPI host from one explicit
`StudioDependencies` container. The container wires settings, an injected
`SDKStudioGateway`, local reference repositories, and Project, Workflow,
Execution, Health, and System services. It creates no provider, V1.x Runtime,
credential, network connection, or background worker.

`StudioSettings.from_mapping()` accepts only declared application metadata,
environment, host/port, debug/docs flags, API prefix, CORS origins,
request/execution timeouts, reference storage mode, log level, and session TTL.
It does not read the process environment or `.env` files. The built-in reference
repository mode is `memory` only.

The REST foundation mounts `GET /health`, `GET /system`, project CRUD,
workflow CRUD, and execution create/list/get below `api_prefix`. Handlers use a
small JSON-compatible controller layer. The lifespan closes a gateway only when
the container explicitly owns it; shutdown is idempotent.

## Release validation

The Studio RC-1 baseline documents offline integration and compatibility checks
in [studio-v2.1-rc1.md](release/studio-v2.1-rc1.md). RC-2 adds bounded local
benchmark, stress, reliability, lifecycle, and cleanup validation in
[studio-v2.1-rc2.md](release/studio-v2.1-rc2.md). Neither release validation
stage changes the Studio product contract or starts a server.
The packaging and fresh-install audit is recorded in
[studio-v2.1-rc3.md](release/studio-v2.1-rc3.md).

FastAPI and Uvicorn remain Studio-host dependencies, not TKAI core
dependencies. After explicitly installing them, `python -m studio.backend`
starts Uvicorn; imports and tests never start a server. No authentication
business logic, database, WebSocket execution, frontend API integration, real
external Provider, or queue is implemented.
