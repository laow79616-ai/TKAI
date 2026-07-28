# Connector Lifecycle

Connectors progress through Draft, Configured, Validated, Enabled, Disabled,
Failed, Deprecated, Archived, and Deleted using the enforced transition table.
Deleted is terminal. Every lifecycle mutation requires RBAC and creates an
audit record.
