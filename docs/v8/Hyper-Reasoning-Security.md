# Hyper Reasoning Security

Read authorization is RBAC-compatible. Scopes enforce tenant, workspace, and
reasoning-namespace isolation. Viewer, auditor, and administrator roles map to
read permissions; metadata registration remains an internal library operation.

Secret filtering is recursive for snapshots, logs, audit metadata, and fabric
metadata. Hidden-reasoning keys are rejected before storage or serialization.
Operators should avoid placing evidence payloads or credentials in any metadata
record and should review audit events for aggregation and registration changes.
