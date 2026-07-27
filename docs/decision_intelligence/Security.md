# Security

Every domain record is bound to a tenant and workspace. Reads and writes enforce
both dimensions and require least-privilege RBAC permissions. Cross-scope access
is denied without revealing record content.

Decision metadata, context, scenarios, and evidence fields reject secret-like
keys. Evidence is represented by opaque references. Audit metadata is sanitized
before storage. Integrations must validate policies before execution and keep
credentials in Enterprise AI Security Platform or the deployment secret store,
never in decision records.
