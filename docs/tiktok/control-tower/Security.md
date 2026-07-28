# Security

Every operation requires tenant, workspace, actor, and an RBAC permission. Results,
alerts, and activity are filtered by tenant and workspace. External references are
stored as scoped opaque digests. Passwords, tokens, cookies, sessions, credentials,
and secrets are rejected from metadata and audit detail and must never be logged.
