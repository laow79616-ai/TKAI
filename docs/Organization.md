# TKAI Enterprise Organization Foundation

## Scope

The Enterprise Organization Foundation provides immutable hierarchy, membership,
and context contracts for TKAI Enterprise V3.0. It reuses the existing
architecture-level `Organization`, `Department`, `Workspace`, and `Team`
descriptors rather than introducing duplicate entities.

No database, repository implementation, authentication, authorization
enforcement, tenant persistence, network request, disk write, or background
worker is implemented in this Sprint. Runtime, SDK, Studio, and Studio REST
remain unchanged.

## Architecture

```text
Explicit caller
    -> OrganizationContext
    -> OrganizationRegistry (optional explicit lookup)
    -> ReferenceOrganization
    -> immutable OrganizationGraph
```

All state is passed explicitly. The Foundation creates no hidden default
organization, reads no environment configuration, and starts no threads.

## Organization and Hierarchy

The hierarchy describes an organization root and optional child entities:

- `Organization`
- `Division`
- `Department`
- `Workspace`
- `Team`

`OrganizationGraph` is an immutable parent/child snapshot. It validates that
parents and children exist, rejects self-child links, and rejects a child with
multiple parents. It is not a graph database, repository, workflow engine, or
authorization system.

## Membership

`Membership` links an explicitly supplied principal identifier to an
organization, optional workspace/team, and declarative role identifiers. It
does not authenticate the principal, resolve an Identity provider, grant
permissions, or enforce access.

## Context and Descriptor

`OrganizationContext` explicitly carries organization, workspace, team, and
membership identifiers for a caller operation. `OrganizationDescriptor`
declares an organization identifier, name, optional capabilities, and safe
metadata. Both are frozen and provide defensive metadata snapshots.

## Reference Organization

`ReferenceOrganization` and `OrganizationFactory` provide deterministic,
in-memory components for tests and examples. `OrganizationRegistry` is a
thread-safe, caller-managed lookup registry with stable ordering. These types
are reference-only and never persist state.

## Policy Boundary

`OrganizationPolicy` is a Protocol for an explicitly invoked hierarchy
validation policy. No policy implementation automatically changes Platform,
Runtime, SDK, Studio, tenant, or authorization behavior.

## Current Limitations

- No database, ORM, repository, cache, or persistence.
- No authentication, identity lookup, role enforcement, or RBAC enforcement.
- No tenant persistence, audit logging, licensing, cloud integration, or
  network access.
- No automatic hierarchy synchronization or background cleanup worker.
