# Security

Every operation requires an explicit RBAC grant. Sessions are isolated by tenant
and workspace, all privileged actions are audited, and configurable limits bound
subtasks, reasoning depth, and simulation counts. APIs use the authenticated actor
scope supplied by the host platform; production deployments should resolve that
scope from trusted authentication middleware.
