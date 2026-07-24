# TKAI Cloud Project Foundation

## Scope

The Cloud Project Foundation is a typed, offline, reference-only layer above
the Workspace Foundation. It adds immutable projects and their explicit
relationships without changing Runtime, SDK, Studio, Enterprise, or existing
Cloud architecture contracts.

No database, ORM, network client, Cloud provider, deployment, storage, billing,
execution, disk state, or background thread is implemented.

## Project model

`Project` is immutable and JSON-safe. It declares `project_id`, `workspace_id`,
name, deterministic slug, description, status, tags, metadata, and UTC
creation/update timestamps. Metadata is defensively copied and no credential
field exists.

`ProjectContext` is always caller-provided. It carries optional account,
workspace, request, and correlation identifiers without using global context or
environment discovery.

## Relationships and policy

`WorkspaceProjectBinding` declares workspace ownership. A workspace can have
many projects, while `ProjectMembershipDescriptor` remains project-local: no
workspace permission is inferred or copied. `ProjectHierarchy` and
`ProjectGraph` produce stable, serializable reference projections.

`ProjectPolicy` is a validation contract only. Its creation, update, context,
and binding methods return `ProjectValidation` containing `valid`, `warnings`,
and `reasons`; they do not enforce access or change state.

## Reference implementation

`ReferenceProjectService` composes an explicit `ProjectFactory` and
thread-safe, in-memory `ProjectRegistry`. It creates, lists, snapshots, and
clears local descriptors and memberships. It does not query a Workspace
Registry or grant workspace permissions, keeping the relationship declarative.

## Current limitations

- No Project Service backed by a database or ORM.
- No deployment, execution, storage, billing, or Cloud provider integration.
- No project update workflow, network API, authorization enforcement, or
  identity lookup.
