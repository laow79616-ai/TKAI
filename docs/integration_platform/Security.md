# Security

Every resource is tenant- and workspace-scoped and every operation is protected
by RBAC. Secrets are opaque references and never enter audit records. Connectors
provide allowlist and payload bounds. Webhooks use signature validation and
replay protection. Database access is read-only by default. Audit events contain
identifiers and outcomes, never payloads, headers, credentials, or secret values.
