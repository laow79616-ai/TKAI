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

The initial REST inventory contains Project, Workflow, Execution, Health, and
System endpoints. The WebSocket protocol reserves asynchronous execution-event
delivery, without starting a server or socket loop.

## Frontend

`studio/frontend` contains a React + TypeScript scaffold with a typed page
inventory for Dashboard, Projects, Workflow, Agents, Providers, Memory, Tools,
Plugins, Settings, and Logs. It includes no build output, dependency lockfile,
or implemented drag-and-drop designer.

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
