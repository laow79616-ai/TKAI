# Memory Security

All service operations require explicit RBAC grants. Tenant and workspace
isolation are mandatory; private memories also enforce owner isolation, while
shared memories remain visible only inside their tenant/workspace. Metadata
secrets must be `secret://` references. `EncryptionProvider` defines the
envelope-encryption integration boundary. Authorization and lifecycle actions
are recorded in the audit stream.
