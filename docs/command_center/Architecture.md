# Enterprise AI Command Center Architecture

The `command_center` package is a framework-neutral operational control plane.
It aggregates existing TKAI platforms through typed projections; it does not
replace their ownership or execution boundaries. `CommandCenterPlatform`
provides scoped domain services, `CommandCenterAPI` exposes read projections,
and the dashboard renders the same API contract.

All records carry tenant and workspace identifiers. Mutations enforce RBAC,
scope checks, audit emission, approval policies, and secret redaction. The
reference implementation is in-memory and can be adapted to durable stores
without changing the domain or API contracts.
