# Enterprise AI Operations Platform Architecture

The operations platform is a tenant- and workspace-scoped control plane for the
TKAI application, agent, workflow, model, knowledge, plugin, and infrastructure
ecosystem. `OperationsPlatform` owns domain state and policy enforcement;
`operations_platform.api` exposes framework-neutral FastAPI route registration;
the dashboard contract exposes consistent read models; and adapters can persist
state or connect monitoring, schedulers, notification transports, and approval
systems without placing credentials in domain objects.

All reads and mutations validate tenant/workspace scope. RBAC separates read,
write, and execute permissions. Upgrade, rollback, and non-preview restore
operations require an external approval reference. Every administrative change
is audited. Operational metrics use stable Prometheus-compatible names.
