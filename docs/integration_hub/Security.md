# Security

Every read and write is tenant/workspace scoped and RBAC protected. Credential
objects contain opaque references only. Payload limits and secret-key detection
protect execution and logs. Audit metadata is filtered for secret-like keys.
Connector adapters must enforce configured destination allowlists and rotation.
