# TKAI Cloud Platform 2.0 Architecture

## Scope

TKAI Cloud is a future product layer above TKAI Platform Enterprise 1.0. This
sprint provides only typed, immutable architecture contracts. It does not
modify Runtime, SDK, Studio, Enterprise, their public APIs, or default
behaviour.

Cloud integrations must use explicit Platform gateways. Importing `cloud` does
not start a server, read configuration or credentials, access a database, open
a network connection, or deploy anything.

## Architecture

```text
Cloud API / Gateway (future, explicit)
             |
             v
Workspace -> Project -> Deployment -> Execution
             |
             +-> Storage descriptor
             |
             +-> Platform Gateway -> Platform Enterprise 1.0
```

`CloudContext` carries account, workspace, project, organization, request, and
correlation scope explicitly. `CloudConfiguration` is an immutable descriptor
for a future host; it performs no environment-variable loading.

## Contracts

- `CloudGateway` and `PlatformGateway` define explicit future invocation
  boundaries.
- `CloudAPI` defines a transport-neutral future API for workspace, project,
  deployment, and execution queries.
- `StorageService` declares storage lookup without implementing filesystem,
  database, or object storage access.
- `BillingService` and `OrganizationService` are reserved interfaces only.

## Models

`Account`, `Workspace`, `Project`, `Deployment`, `Execution`, and
`StorageDescriptor` are frozen, defensive descriptors. Deployment and execution
statuses describe external lifecycle state but never cause lifecycle actions.

See [Workspace Foundation](Workspace.md) for the additive local workspace,
membership, invitation, registry, and graph reference contracts.

See [Project Foundation](Project.md) for immutable project descriptors,
workspace/project bindings, project-local membership declarations, and the
in-memory reference registry.

See [Deployment Foundation](Deployment.md) for reference-only deployment plans,
targets, lifecycle declarations, and local test service.

See [Storage Foundation](Storage.md) for in-memory storage descriptors and
reference bucket/object lifecycle contracts.

See [Execution Foundation](Execution.md) for reference execution descriptors,
history, lifecycle validation, and in-memory service contracts.

See [Platform Gateway](PlatformGateway.md) for explicit Cloud-to-Platform
adapter contracts and reference capability/version/health descriptors.

## Current limitations

- No Cloud server, REST transport, database, queue, object store, or Kubernetes
  implementation.
- No billing calculation, charge, invoice, account login, or organization
  resolution.
- No real deployment, execution scheduling, credential handling, or network
  access.
- No automatic integration with Platform layers.
