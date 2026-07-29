# Security

State operations are compatible with V7 deny-by-default RBAC. Optional
`AccessController` integration enforces capabilities. Tenant, workspace, and
owner checks prevent cross-scope access. Secret-like metadata is recursively
redacted before storage, tracing, history, API, or dashboard projection.
