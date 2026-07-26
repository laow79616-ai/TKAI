# Security

Every model resource is tenant- and workspace-isolated. RBAC covers read, write,
approval, routing, deployment, evaluation, governance, invocation, and
administration. Provider and model allowlists are enforced at route and invoke
time. Credential references are opaque, provider metadata rejects secret-like
fields, and audit metadata redacts secret, token, password, API-key, and
credential fields.
