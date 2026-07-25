# TKAI Cloud Workspace Foundation

## Scope

The Cloud Workspace Foundation is an offline reference layer for Cloud Platform
2.0. It adds workspace descriptors, local reference membership state, and graph
projections without changing Runtime, SDK, Studio, Enterprise, or their public
APIs.

No database, network, cloud provider, storage backend, project service,
deployment service, billing service, or invitation delivery is implemented.

## Architecture

```text
Account
  └─ Workspace
       ├─ Membership -> Principal descriptor
       ├─ Invitation -> Principal descriptor
       └─ Workspace Graph snapshot
```

`Workspace` and `Project` remain the immutable Cloud architecture models.
`WorkspaceContext` supplies caller-owned scope. `WorkspaceDescriptor` and
`WorkspacePolicy` declare future capabilities and policy boundaries without
enforcing access.

## Reference implementation

`ReferenceWorkspaceService` composes an explicit `WorkspaceFactory` and
thread-safe `WorkspaceRegistry`. It supports bounded local creation, lookup,
membership recording, invitation declaration, and idempotent cleanup. It never
contacts an identity provider, sends an invitation, or persists data.

`WorkspaceGraph` produces a stable, JSON-safe account/workspace/principal graph
snapshot for callers that need a reference projection.

## Current limitations

- No Project Service or project lifecycle implementation.
- No invitation acceptance, expiry worker, email, or notification transport.
- No authorization enforcement, identity lookup, or organization resolution.
- No persistence, database, cloud provider, deployment, storage, or billing
  backend.
